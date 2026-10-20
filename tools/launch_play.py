"""Run an Isaac Lab script with h5py loaded first.

Why: h5py ships its own hdf5.dll, and Isaac Sim's RTX-sensor extension ships a different one.
Windows loads a DLL by name once per process, so whichever loads first wins. In GUI mode Kit
starts the RTX-sensor extension before Isaac Lab imports h5py, and h5py then fails with
"The specified procedure could not be found". Importing h5py first flips the order: h5py works,
and the RTX-sensor extension fails to import instead (harmless unless the task uses RTX
lidar/radar).

Usage:
    python tools/launch_play.py <script.py> [script args...]
"""

import os
import runpy
import sys

import h5py  # noqa: F401  (must be the first non-stdlib import)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    script = os.path.abspath(sys.argv[1])
    # The target script imports siblings (e.g. cli_args.py); runpy doesn't add its folder.
    sys.path.insert(0, os.path.dirname(script))
    sys.argv = sys.argv[1:]
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
