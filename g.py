import os

parentdir = os.path.abspath(os.curdir)
chdir = parentdir+"/ddllc"
wsgi_app = "index:base"
reload = True
reloadengine = "inotify"
keyfile = parentdir +"/privkey1.pem"
certfile =  parentdir+"/fullchain1.pem"
bind = "0.0.0.0:8000"
workers = "2"
worker_class = "gevent"
