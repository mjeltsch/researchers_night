# researchers_night
Python script to automatically upload images to a Piwigo server

This script automatically uploads images taken with the digital cameras on our Leica microscopes to a Piwigo gallery. However, it only monitors a specific folder, and whenever new files appear, it tries to upload them. It requires locally installed Python (with the following dependencies: pip install watchdog requests) and admin access to a Piwigo server.
