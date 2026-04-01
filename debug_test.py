import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_module.core.detector import run_frame_processing

video = "ai_module/test_videos/Cattle_shed_at_night.mp4"
if os.path.exists(video):
    print("Found video")
else:
    print("Video not found")

try:
    gen = run_frame_processing(video)
    frame, entry, total = next(gen)
    print(f"Success! frame size {len(frame)}, entry {entry}, total {total}")
except Exception as e:
    import traceback
    traceback.print_exc()
