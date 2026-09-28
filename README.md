# researchers_night
Python script to automatically upload images to a Piwigo server

This script automatically uploads images taken with the digital cameras on our Leica microscopes (using this software: https://www.leica-microsystems.com/products/microscope-software/p/leica-las-ez/downloads/) to a Piwigo gallery. However, it only monitors a specific folder, and whenever new files appear, it tries to upload them. Hence, it can be used to monitor any folder for incoming images. It requires locally installed Python (with the following dependencies: pip install watchdog requests) and admin access to a Piwigo server.
