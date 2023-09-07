#!/bin/bash
cd /data/project/imagehash/www/python/Imagehash-Toolforge/indexing
python3 -m venv venv_311
source ./venv_311/bin/activate
pip3 install -r requirements.txt 
echo "Running the script"
nice python3 insert_phash_and_dhash_rc_v1el2_kubernetes.py
