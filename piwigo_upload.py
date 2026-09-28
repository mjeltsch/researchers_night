import time
import os
import requests
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

# LINUX
# Run the script like this: nohup python3 piwigo_upload.py > upload.log 2>&1 &
# Stop the script like this: pkill -f piwigo_upload.py
# View logs: tail -f upload.log
#
# WINDOWS
# Run the script from PowerShell: Start-Process pythonw -ArgumentList "piwigo_upload.py"
# Stop the script via the Task Manager (Ctrl + Shift + Esc)

# --- Configuration ---
WATCH_DIR = "/home/user/Pictures/PiwigoUploads"
PIWIGO_URL = "https://images.piwigoserver.org/ws.php?format=json"
PIWIGO_USER = "replace this with your username" 
PIWIGO_PASSWORD = "replace this with your password" 
CATEGORY_ID = 1 
# ---------------------

class UploadEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            filename = os.path.basename(file_path)
            
            print(f"-> [1/4] New file detected: {filename}")
            print(f"-> [2/4] Waiting 2 seconds for disk write to complete...")
            
            time.sleep(2) 
            
            try:
                with requests.Session() as session:
                    print(f"-> [3/4] Logging into Piwigo API...")
                    login_data = {
                        'method': 'pwg.session.login',
                        'username': PIWIGO_USER,
                        'password': PIWIGO_PASSWORD
                    }
                    response = session.post(PIWIGO_URL, data=login_data)
                    try:
                        login_response = response.json()
                    except Exception as e:
                        print(f"❌ Server returned a non-JSON response. HTTP Status: {response.status_code}")
                        print(f"Raw server response: \n{response.text[:500]}")
                        return
                    
                    if login_response.get('stat') != 'ok':
                        print(f"❌ Login failed: {login_response.get('message', 'Unknown error')}\n")
                        return

                    # Fetch the required pwg_token for publishing/completion methods
                    status_data = {'method': 'pwg.session.getStatus'}
                    status_resp = session.post(PIWIGO_URL, data=status_data)
                    pwg_token = None
                    try:
                        status_json = json.loads(status_resp.text[status_resp.text.find('{'):])
                        if status_json.get('stat') == 'ok':
                            pwg_token = status_json.get('result', {}).get('pwg_token')
                    except Exception:
                        pass

                    print(f"-> [4/4] Uploading {filename} to category ID {CATEGORY_ID}...")
                    upload_data = {
                        'method': 'pwg.images.addSimple',
                        'category': CATEGORY_ID,
                        'name': filename
                    }
                    with open(file_path, 'rb') as f:
                        files = {'image': f}
                        upload_req = session.post(PIWIGO_URL, data=upload_data, files=files)
                    
                    try:
                        upload_response = upload_req.json()
                        if upload_response.get('stat') == 'ok':
                            image_id = upload_response.get('result', {}).get('image_id')
                            print(f"✅ Success: {filename} uploaded and added to the gallery. (ID: {image_id})")
                            
                            if image_id:
                                # 1. Publish from lounge with the required token included
                                print(f"-> Publishing image from the lounge...")
                                complete_data = {
                                    'method': 'pwg.images.uploadCompleted',
                                    'image_id': image_id,
                                    'category_id': CATEGORY_ID,
                                    'pwg_token': pwg_token
                                }
                                session.post(PIWIGO_URL, data=complete_data)
                                
                                # 2. Force-generate thumbnails
                                print(f"-> Force-generating thumbnails for image ID {image_id}...")
                                info_data = {
                                    'method': 'pwg.images.getInfo',
                                    'image_id': image_id
                                }
                                info_req = session.post(PIWIGO_URL, data=info_data)
                                
                                json_start = info_req.text.find('{')
                                if json_start != -1:
                                    info_response = json.loads(info_req.text[json_start:])
                                    if info_response.get('stat') == 'ok':
                                        derivatives = info_response.get('result', {}).get('derivatives', {})
                                        
                                        for size, data in derivatives.items():
                                            if isinstance(data, dict) and 'url' in data:
                                                print(f"   - Processing size: {size}")
                                                session.get(data['url'])
                                        
                                        now = datetime.now()
                                        print("✅ All thumbnails successfully pre-generated and published instantly at {0}.\n".format(now))                        
                        else:
                            print(f"❌ Upload failed: {upload_response.get('message', 'Unknown error')}\n")
                    except Exception as e:
                        print(f"❌ Server returned a non-JSON response during upload. HTTP Status: {upload_req.status_code}")
                        print(f"Raw server response: \n{upload_req.text[:500]}\n")

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}\n")

if __name__ == "__main__":
    print(f"Starting API directory monitor on: {WATCH_DIR}")
    print("Waiting for new files... (Press Ctrl+C to stop)\n")
    
    event_handler = UploadEventHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping script...")
        observer.stop()
    observer.join()