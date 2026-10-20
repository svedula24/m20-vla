# Isaac Sim + Isaac Lab on native Windows 11

Machine: RTX 5090 Laptop (Blackwell, sm_120, 24 GB), driver 591.83, Core Ultra 9 386H, 32 GB RAM
(soldered). Verified 2026-10-08, re-verified 2026-10-20.

## Versions

| Component | Version |
|---|---|
| Python | 3.11 (conda-forge) |
| Isaac Sim | 5.1.0 (`pip install "isaacsim[all,extscache]==5.1.0"`) |
| Isaac Lab | v2.3.2, editable install from a checkout |
| torch / torchvision / torchaudio | 2.7.0+cu128 / 0.22.0+cu128 / 2.7.0+cu128 |
| rsl-rl-lib | 3.1.2 |
| tensordict | 0.8.3 (pinned; 0.14.x crashes on import with torch 2.7) |

Driver note: stay on 591.x with Isaac Sim 5.1 or 6.0.0. 6.0.1 and 6.1 want driver 595.97, and
the 595 branch has a confirmed Vulkan crash on Blackwell laptops.

## Environment

- Miniconda per-user at `%USERPROFILE%\miniconda3`.
- The env lives at a **short prefix** `C:\ce\isaaclab` on purpose: Windows long paths are off and
  the Isaac Sim extscache wheels exceed MAX_PATH under `...\miniconda3\envs\isaaclab`. `envs_dirs`
  in `~\.condarc` has `C:\ce` prepended so `conda activate isaaclab` resolves there.
- `OMNI_KIT_ACCEPT_EULA=YES` is stored as a conda env var on the env.
- Pins in `C:\ce\constraints.txt`; pass `-c C:\ce\constraints.txt` to any future `pip install`:
  torch/vision/audio 2.7.0 cu128, numpy 1.26.0, psutil 5.9.8, click 8.1.7, starlette 0.49.1,
  rsl-rl-lib 3.1.2, tensordict 0.8.3.

Activate (PowerShell, no `conda init` needed):

```powershell
& "$env:USERPROFILE\miniconda3\shell\condabin\conda-hook.ps1"; conda activate isaaclab
```

**Activate properly.** Putting `C:\ce\isaaclab` and `...\Library\bin` on PATH by hand is not
enough: h5py fails with a DLL error. `conda activate` sets what the DLLs need.

## Launch

Isaac Sim GUI (full app):

```powershell
isaacsim isaacsim.exp.full.kit
```

Takes ~36 s to "app ready" after the first (shader-cache) launch. ~8 GB resident with an RL env.

Isaac Lab script in GUI mode: use `tools\launch_play.py` (see its docstring for the h5py /
RTX-sensor DLL clash). Headless scripts don't need it.

## Memory

RAM is the limit, not VRAM. The WSL demo stack takes 16 GB (`.wslconfig`); Isaac and WSL do not
fit together. `wsl --shutdown` first. Measured with WSL running, `--headless`:

| num_envs | peak GPU used (total) | python working set | python commit |
|---|---|---|---|
| 64 | 5.6 GB | 4.7 GB | 9.3 GB |
| 4096 | 7.7 GB | 6.1 GB | 13.2 GB |

## Known quirks

- Redirecting stdout to a file: set `PYTHONUNBUFFERED=1`. Kit hard-exits on close and drops
  buffered output.
- `SimulationApp.close()` can hang after all work is done. If a run sits at shutdown, the
  checkpoints are already saved; kill it.
- Isaac Lab `--install` fails to build `flatdict` with new setuptools (`pkg_resources` gone):
  `pip install "setuptools<81"` then `pip install --no-build-isolation flatdict==4.0.1`.
- rl_training HEAD imports `handle_deprecated_rsl_rl_cfg`, which only exists in Isaac Lab newer
  than v2.3.2. Guard the import with an identity fallback (not Windows-specific).
