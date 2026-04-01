#!/usr/bin/env bash
# exit on error
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Install OpenCV system dependencies (required for YOLOv8)
# If Render environment supports apt-get
apt-get update && apt-get install -y libgl1-mesa-glx
