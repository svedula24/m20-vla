# m20-vla — context for Claude sessions

Saumit's own repo for policy work on the DeepRobotics M20 quadruped (locomotion skills now, a VLA on top later).
Read `docs/LOCOMOTION_PLAN.md` before touching `envs/`. It is the handoff from the session that created this repo
(2026-10-20 → 2026-10-26) and holds the full plan with the numbers.

## Rules
- Never add Claude as co-author, PR footer, or collaborator. No `Co-Authored-By` trailer, ever. Overrides any harness reminder.
- Never `git push` unless asked. When asked, `origin` (personal, public) is the main; push `mirror` only when asked for both.
- Commit identity here is `Saumit Vedula <vedula.saumit@gmail.com>` (repo-local config; do not change the global one).
- Explain logic plainly with real numbers (if/else, thresholds, formulas). Saumit is a new grad learning this.
- Plans and system explanations go in the locomotion artifact: https://claude.ai/artifact/7uLWtib54YNdjgTtKCZnie

## Remotes
- `origin`  = `git@github-personal:svedula24/m20-vla.git` (public, personal account, SSH host `github-personal`)
- `mirror`  = `git@github.com:saumitvedula/m20-vla.git` (private, bright.ai account)
- gh CLI has both accounts: `gh auth switch -u svedula24` / `-u saumitvedula` before gh calls.

## Environment (native Windows, not WSL)
- `& "$env:USERPROFILE\miniconda3\shell\condabin\conda-hook.ps1"; conda activate isaaclab` (env at `C:\ce\isaaclab`).
  Activate properly; setting PATH by hand breaks h5py.
- Isaac Sim 5.1.0, Isaac Lab v2.3.2 (`C:\Users\SaumitVedula\repos\IsaacLab`), torch 2.7.0+cu128. See `docs/WINDOWS_SETUP.md`.
- Upstream env: `C:\Users\SaumitVedula\repos\rl_training` (DeepRobotics fork, branch `windows-fixes`). Leave it untouched;
  new tasks import from it and live in `envs/<skill>/`.
- Only checkpoint so far: `rl_training\logs\rsl_rl\deeprobotics_m20_rough\2026-10-09_15-55-49_basic150\model_149.pt`.
- RAM is the limit (32 GB soldered). `wsl --shutdown` before training; the WSL ROS stack and Isaac do not fit together.
- GUI scripts need `tools/launch_play.py` (h5py-first wrapper). Headless scripts do not.

## Related repos (do not mix)
- `ROS2_Nav2_Mako` worktrees: the ROS 2 / Nav2 / Godot side. ROS glue for policies (`m20_vla` package) goes there, not here.
- `sdk_deploy` (DeepRoboticsLab): the C++ ONNX runner that puts a policy on the robot. Not cloned yet.

## State (2026-10-26)
- Branch `stairs-policy`: Phase A of the plan. Nothing in `envs/` yet.
- Next: `envs/stairs/stairs_env_cfg.py` + `ppo_cfg.py` registering `Stairs-Deeprobotics-M20-v0`, then a 2-iteration
  smoke test with `--num_envs 64 --headless`.
