#!/usr/bin/env python2

try:
    # Python 3
    from http.server import SimpleHTTPRequestHandler
except ImportError:
    # Python 2
    from SimpleHTTPServer import SimpleHTTPRequestHandler
try:
    # Python 3
    from socketserver import TCPServer
except ImportError:
    # Python 2
    from SocketServer import TCPServer
import socket
import logging
import sys
try:
    # Python 3
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse
try:
    # Python 3
    from urllib.parse import unquote
except ImportError:
    # Python 2
    from urlparse import unquote
try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs

from datetime import datetime
from jinja2 import Template
import csv
import re
from collections import defaultdict
import signal


try:
    PORT = int(sys.argv[1])
except:
    PORT = 8000

LOG_PATH = '/tmp'
TEMPLATE_FILE = 'templates/assignment.html.j2'
TEMPLATE_DONE = 'templates/do_assignment.html.j2'
SOURCE_FILE = 'test.csv'

ASSIGNMENT_PATH='/tmp'

class reuseTCPServer(TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

class quietServer(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if bool(re.match(r"^/do_assignment.html.*", self.path)):
            # Parse the URL and extract the arguments we're interested in
            parsed_path = urlparse(self.path)
            site_name = parse_qs(parsed_path.query)['site_name'][0]
            site_id = parse_qs(parsed_path.query)['site_id'][0]
            mac_address = parse_qs(parsed_path.query)['mac_address'][0]

            # Set the filename
            filename = ASSIGNMENT_PATH + '/' + mac_address + ".assignment"

            file_contents = "SITE_NAME=" + site_name + "\n"
            file_contents += "SITE_ID=" + site_id + "\n"
            file_contents += "MAC_ADDRESS=" + mac_address + "\n"

            # Open the assignment file in overwrite mode
            f = open(filename, "w")
            # Write the content defined earlier to the file and close the file handle
            f.write(file_contents)
            f.close()

            # So that the user gets presented with an appropriate status page, use another template
            # to share the variables we set so they can sanity check
            with open(TEMPLATE_DONE) as tf:
                template = Template(tf.read(), keep_trailing_newline=True)

            assignment_config = template.render(filename=filename, file_contents=file_contents)
            assignment_config += '\n'

            # Sending an '200 OK' response
            self.send_response(200)

            # Setting the header
            self.send_header("Content-type", "text/html")

            # Whenever using 'send_header', you also have to call 'end_headers'
            self.end_headers()

            # Compatible with both Python 2 and 3
            self.wfile.write(bytes(assignment_config.encode("utf8")))

        elif self.path == '/assignment.html':
            # Read in the template file for rendering later
            with open(TEMPLATE_FILE) as tf:
                template = Template(tf.read(), keep_trailing_newline=True)

            # Initialize a blank dicitionary before we read the CSV file - we're using an append operation
            # with the rows, so the dictionary must be blank, or odd behaviour will occur if the CSV is changed
            # whilst this script is running
            columns = defaultdict(list)

            # Read the CSV file and create a dictionary of columns so that we can extract unique names/values
            with open(SOURCE_FILE) as sf:
                reader = csv.DictReader(sf)
                for row in reader:
                    for (key, value) in row.items():
                        columns[key].append(value)

            # Extract the unique site names into a list using a set
            site_names = list(set(columns['site name']))
            site_ids = list(set(columns['site id']))

            # Sort the lists to make the drop downs more friendly
            site_names.sort()
            site_ids.sort()

            # Render the Jinja2 template for output over the HTTP server
            site_config = template.render(site_names=site_names, site_ids=site_ids)
            site_config += '\n'

            # Sending an '200 OK' response
            self.send_response(200)

            # Setting the header
            self.send_header("Content-type", "text/html")

            # Whenever using 'send_header', you also have to call 'end_headers'
            self.end_headers()

            # Compatible with both Python 2 and 3
            self.wfile.write(bytes(site_config.encode("utf8")))
        # Assume anything else is for logging...
        else:
            parsed_path = urlparse(self.path)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
 
            try:
                MAC = parsed_path.path.split('/')[1]
                LOGMSG = unquote(parsed_path.path.split('/')[2])
            except:
                msg_url_error = "Error in URL encoding for logging - no action will be taken...\n"
                self.wfile.write(bytes(msg_url_error.encode("utf8")))
            else:
                #f = open(self.address_string() + ".txt", "a")
                filename = LOG_PATH + '/' + MAC + ".txt"
                f = open(filename, "a")

                f.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " - " + LOGMSG + "\n")
                f.close()

                msg_url_ok = "URL data was successfully logged to " + filename + "\n"
                self.wfile.write(bytes(msg_url_ok.encode("utf8")))


def signal_handler(sig, frame):
    print('Shutting down...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

httpd = reuseTCPServer(("", PORT), quietServer)
httpd.allow_reuse_address = True
httpd.serve_forever()

