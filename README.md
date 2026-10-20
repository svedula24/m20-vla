# m20-vla

Vision-language-action (VLA) policy work for the DeepRobotics M20 quadruped: simulation tasks, data
collection, model training, and an inference server that a ROS 2 integration can call.

This repo is the **policy side**. Deployment on the robot and the Godot/ROS 2 sim evals live in
`ROS2_Nav2_Mako` (`m20_vla` package there calls the inference server from `serve/`).

## Layout

| Folder | What goes here |
|---|---|
| `envs/` | Simulator tasks (currently Isaac Lab; simulator choice is open, see below) |
| `data/` | Collection scripts and dataset manifests. Datasets themselves are **not** committed |
| `models/` | Model definitions and checkpoints metadata. Checkpoints are **not** committed |
| `training/` | Training and eval scripts |
| `serve/` | Inference server (HTTP), the boundary the ROS 2 side talks to |
| `tools/` | Launchers and one-off helpers |
| `docs/` | Setup notes |

## Current base

- Low-level locomotion: the rsl_rl policy from DeepRobotics `rl_training` (checkpoint `basic150`,
  `Rough-Deeprobotics-M20-v0`). This repo builds nav-level actions on top of it.
- Simulator: Isaac Sim 5.1 + Isaac Lab 2.3.2 on native Windows for now. See `docs/WINDOWS_SETUP.md`.
  A switch to a simulator more common for VLA work is planned.

## Run

```powershell
& "$env:USERPROFILE\miniconda3\shell\condabin\conda-hook.ps1"; conda activate isaaclab
python tools\launch_play.py <path-to-rl_training>\scripts\reinforcement_learning\rsl_rl\play.py `
    --task=Rough-Deeprobotics-M20-v0 --num_envs 16 --checkpoint <abs path to model_149.pt> --real-time
```
