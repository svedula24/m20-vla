# M20 locomotion policies — plan and handoff

Written 2026-10-26 as the handoff from the session that created this repo. The same content, formatted, is the
artifact https://claude.ai/artifact/7uLWtib54YNdjgTtKCZnie. Numbers below come from the config files on this laptop.

## 1. Where we start

`rl_training` gives one M20 task, `Rough-Deeprobotics-M20-v0`: a velocity-tracking policy (input: desired speed;
output: joint targets; reward: match the speed without falling). It already trains on stairs but is not a stair policy.

| Fact | Today | Why it matters |
|---|---|---|
| Terrain | `ROUGH_TERRAINS_CFG`: 10 rows × 20 cols of 8×8 m tiles; 20 % stairs up, 20 % stairs down (rise 5→23 cm), 20 % boxes, 20 % rough, 20 % slopes. `max_init_terrain_level=5`. | Stairs exist. Curriculum `terrain_levels_vel` promotes a robot that walks > half the tile, demotes one covering < half its commanded distance. |
| Actor obs | ang vel (3), gravity (3), command (3), 16 joint pos, 16 joint vel, last action (16). `height_scan = None` (rough_env_cfg.py:110). Critic sees the 1.6×1.0 m grid at 0.1 m (187 rays). | Blind. It finds steps by hitting them. |
| Stepping rewards | `feet_air_time`, `feet_stumble`, `feet_height`, `feet_gait` all weight 0. | Feet are wheels; rolling is cheapest and fails at the first riser. |
| Falls | `illegal_contact = None`, `bad_orientation_2 = None`. | A tipped robot sits out the 20 s episode. |

Robot: 16 joints (12 leg + 4 wheel). Leg PD: stiffness 80, damping 2, 76.4 N·m, 22.4 rad/s, 1-step delay. Wheels:
damping 0.6, 21.6 N·m, 79.3 rad/s. Default X stance: front `hipy −0.6, knee +1.0`, hind `hipy +0.6, knee −1.0`
(vendor "front-elbow, rear-knee"; its stair mode "full-elbow" is never trained in sim).
Action scale: hipx 0.125, other legs 0.25, wheels 5.0 (velocity). Friction randomized 0.35–1.5.
PPO: 4096 envs × 24 steps/iter, lr 1e-3 adaptive, γ 0.99, λ 0.95, MLP [512,256,128] ELU. ~3.1 s/iter on this laptop:
5 000 iters ≈ 4.5 h, 20 000 ≈ 17 h. Only checkpoint: `basic150` (150 iters).

## 2. Roadmap

- **A. One skill: stairs.** New task `Stairs-Deeprobotics-M20-v0`, blind, wheels live, ~5k iters, fits the vendor
  deploy runner unchanged. Output: `stairs.onnx` + a success rate per step height.
- **B. Skill library + switcher.** Add flat-fast; rule-based arbiter (terrain class or command); stop-and-switch
  handoff; extend `rl_deploy` to hold N models + a switch service.
- **C. One generalized policy.** Perceptive, teacher–student, memory in the net, 10–20k iters, needs an elevation map
  on the robot. After B, because the skills become the teachers.
- **D. VLA on top.** VLA outputs skill + velocity command at 1–10 Hz; skills run at 50 Hz; VLA never touches joints.
  Same boundary as `m20_vlmnav` → Nav2 in the Mako repo.

Pipeline: Isaac Lab task → `train.py` → `model_N.pt` → `export_onnx_fast.py` → `sdk_deploy rl_deploy` →
MuJoCo `M20_stair.xml` (5 × 10 cm rise × 30 cm tread, platform at 50 cm) → real M20 (`/JOINTS_CMD` at 50 Hz).

## 3. Phase A: the stairs policy, step by step

1. **Roll vs walk.** Start with wheels live and let rewards push stepping. Fallback if no convergence in 3k iters:
   lock wheels (wheel action scale → 0).
2. **Terrain.** stairs up 30 % (`step_height_range=(0.05, 0.18)`, `step_width=0.28`), stairs down 30 % (same),
   flat 10 %, random rough 15 % (`noise_range=(0.01, 0.10)`), slopes 15 % (`slope_range=(0.0, 0.4)`). Keep 10 rows and
   `max_init_terrain_level=5`.
3. **Keep blind.** `height_scan` stays out of the actor so the vendor's `rl_deploy` (IMU + joints only) runs it unchanged.
4. **Rewards / terminations / commands.**
   - `feet_stumble` 0 → −1.0 (horizontal contact force > 2× vertical = wheel hit a riser)
   - `feet_air_time` 0 → +0.25, threshold 0.5 s
   - `feet_height` 0 → +0.1, target 0.10 m
   - `base_height_l2` −0.5 @ 0.40 m unchanged (already terrain-relative via `height_scanner_base`)
   - `illegal_contact` termination ON: `base_link` + thighs, force > 1 N
   - `lin_vel_x` command (−2, 2) → (−1, 1) m/s; `track_lin_vel_xy_exp` 2.0 unchanged
   - Watch: if it hops on flat, gate air-time/height rewards on terrain or drop them to 0.1 / 0.05.
5. **Train.** `wsl --shutdown`; `train.py --task=Stairs-Deeprobotics-M20-v0 --headless --num_envs 4096
   --max_iterations 5000 --run_name stairs_v1`. Watch mean terrain level (→ 9; plateau at 3–4 = ramp too steep),
   `feet_stumble` (→ 0), episode length (→ 20 s).
6. **Evaluate.** Stairs-only test terrain, rises 10/14/18 cm, 100 episodes each: % reach top, % fall, mean time.
   Baseline = `basic150` on the same terrain.
7. **Export + MuJoCo.** `export_onnx_fast.py`; run in `sdk_deploy` `M20_stair.xml`.
8. **Real robot.** Same `rl_deploy` binary, SDK mode (vendor controller out of the loop). One 10 cm step, on a leash.

## 4. Phase B: handoff between skills

Switch only when all four feet are in contact and |v_cmd| < 0.1 m/s (simplest, enough for stairs). Next:
blend `q = (1−α)·q_old + α·q_new`, α 0→1 over 0.3 s (15 steps at 50 Hz). Then: put each skill's exit states into the
other skill's reset distribution.

## 5. Phase C: generalized policy needs

1. Height scan in the actor (187 values, noise ±0.1, clip ±1) → elevation map from the two LiDARs at ~50 Hz on the robot.
2. Terrain diversity + curriculum to completion (10–20k iters), mix extended to curbs, pipes, gaps.
3. Teacher–student: privileged teacher (true terrain, friction, contacts) → student on real sensors + ~50-step history.
4. Capacity: GRU or 1-D conv over history on top of the MLP.
M20-specific: the policy must learn when to roll vs step; stepping rewards must be conditioned on terrain via the
height scan.

## 6. Decisions (taken)

- Wheels live, fall back to locked. — Blind for A/B, perceptive for C. — Vendor stair mode (implement `request_gait`
  in the Mako bridge) stays the fallback while ours trains. — Code lives here in `envs/<skill>/`; `rl_training`
  stays untouched.

## 7. What DeepRobotics provides

Robot model (`deep_robotics_model`), training env (`rl_training`), C++ ONNX deploy runner + MuJoCo sim-to-sim with a
stair scene (`sdk_deploy/src/M20_sdk_deploy`). NOT provided: a trained M20 policy (Lite3 gets one), any stair-specific
env/rewards, any perception pipeline for a policy. The real robot's stock stair climbing is a closed controller:
wheels lock, legs go "full-elbow", triggered by LiDAR point-cloud detection; rated 25 cm continuous stairs, 80 cm single step.

## 8. Known gotchas

- h5py vs Isaac RTX-sensor `hdf5.dll` clash in GUI mode → `tools/launch_play.py` imports h5py first.
- `play.py --checkpoint` wants an absolute path (not relative to `--load_run`).
- `rl_training` HEAD imports `handle_deprecated_rsl_rl_cfg` (Isaac Lab > 2.3.2) → guarded in the `windows-fixes` branch.
- tensordict must stay 0.8.3; constraints in `C:\ce\constraints.txt`.
