This is web interface for ImageHash-Toolforge which is used to detect if image already exists in Wikimedia Commons.

Howto install to toolforge
- https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool

Prerequisites
# Create toolforge account and request access to imagehash project
# First login to toolforge 

Then 
# become imagehash
# mkdir -p $HOME/www/python
# cd $HOME/www/python
# git clone https://github.com/Wikimedia-Suomi/ImageHash-Toolforge.git
# ln -s ImageHash-Toolforge/web src
# webservice --backend=kubernetes python3.11 shell
# python3 -m venv $HOME/www/python/venv
# source $HOME/www/python/venv/bin/activate
# pip install --upgrade pip
# pip install -r $HOME/www/python/src/requirements.txt
# deactivate
# webservice --backend=kubernetes python3.11 start

Updating pip packages
# webservice --backend=kubernetes python3.11 shell
# source $HOME/www/python/venv/bin/activate
# pip install packagename
# deactivate

Updating code
# cd $HOME/www/python/ImageHash-Toolforge/web
# nano app.py
# webservice restart

Log files
- $HOME/uwsgi.log
- $HOME/error.log

Config files
- $HOME/www/python/src/config.yam
