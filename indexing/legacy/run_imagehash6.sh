#!/bin/bash
cd /data/project/imagehash/t
python3 -m venv venv_311
source ./venv_311/bin/activate
pip3 install toolforge imagehash pillow pywikibot
echo "Running the script"
nice python3 insert_phash_and_dhash_rc_v1el2_kubernetes.py
