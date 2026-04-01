import os
import requests

from app import create_app

app = create_app()

with app.app_context():
    # simulate file creation
    upload_folder = os.path.join(os.path.dirname(__file__), "static/uploads")
    os.makedirs(upload_folder, exist_ok=True)
    import shutil
    shutil.copy("ai_module/test_videos/Cattle_shed_at_night.mp4", os.path.join(upload_folder, "test_req.mp4"))

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['owner'] = 'test_owner'

    res = client.get('/live_upload_stream/test_req.mp4', stream=True)
    print("STATUS", res.status_code)
    try:
        content_iter = res.iter_encoded()
        for i in range(5):
            print("Iteration", i, next(content_iter)[:40])
    except Exception as e:
        print("ERROR:", e)
