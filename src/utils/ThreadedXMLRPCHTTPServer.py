from http.server import HTTPServer
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer
from defusedxml.xmlrpc import xmlrpc_server

from settings.settingsprovider import SettingsProvider


class ThreadedXMLRPCHTTPServer(ThreadingMixIn, HTTPServer, xmlrpc_server.SimpleXMLRPCServer):
    def __init__(self, handler, port=None, listen_localhost=False):
        host = '0.0.0.0' if not listen_localhost else '127.0.0.1'
        if not port:
            port = int(SettingsProvider.get_instance().read_setting('listenporthttp'))
        HTTPServer.__init__(self, (host, port), handler, )
        SimpleXMLRPCServer.__init__(self, (host, port), handler, allow_none=True)
