#!/usr/bin/env python2

try:
    from http.server import SimpleHTTPRequestHandler
except ImportError:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
try:
    from socketserver import TCPServer
except ImportError:
    from SocketServer import TCPServer
import logging
import sys
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
try:
    from urllib.parse import unquote
except ImportError:
    from urlparse import unquote
from datetime import datetime

try:
    PORT = int(sys.argv[1])
except:
    PORT = 8000

LOG_PATH = '/var/www/buildlogger'

class quietServer(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed_path = urlparse(self.path)
        self.send_response(200)
        self.end_headers()

        MAC = parsed_path.path.split('/')[1]
        LOGMSG = unquote(parsed_path.path.split('/')[2])

        #f = open(self.address_string() + ".txt", "a")
        f = open(LOG_PATH + '/' + MAC + ".txt", "a")

        f.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " - " + LOGMSG + "\n")
        f.close()
try:
    with TCPServer(("", PORT), quietServer) as httpd:
        httpd.serve_forever()
except:
    httpd = TCPServer(("", PORT), quietServer)
    httpd.serve_forever()

