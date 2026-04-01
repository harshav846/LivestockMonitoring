#!/usr/bin/env bash
# exit on error
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Install OpenCV system dependencies (using headless python-opencv instead)
# python -m pip install -r requirements.txt handles this.
