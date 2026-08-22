# Vendor wheels (offline Mac)

On a networked Mac with the same macOS and Python version:

1. Double-click `../Prepare Offline Wheels.command`, or run:
   `python3 -m pip download -r ../requirements.txt -d .`
2. Copy the whole Secret Kit folder (including this `vendor/` directory) to the offline Mac.
3. Double-click `Start Secret Kit.command`. It creates `.venv` from these wheels and never talks to PyPI.

