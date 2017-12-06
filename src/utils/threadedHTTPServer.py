#
#	Multi-thread HTTPServer class
#

from socketserver import ThreadingMixIn
from http.server import HTTPServer


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass