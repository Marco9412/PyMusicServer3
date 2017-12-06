import ssl
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer
from defusedxml.xmlrpc import xmlrpc_server

from settings.settingsprovider import SettingsProvider


# class SecureThreadedXMLRPCHTTPServer(ThreadingMixIn, HTTPServer, SimpleXMLRPCServer):
class SecureThreadedXMLRPCHTTPServer(ThreadingMixIn, HTTPServer, xmlrpc_server.SimpleXMLRPCServer):
    def __init__(self, handler, certFile=None, port=None):
        if not certFile:
            certFile = SettingsProvider.get_instance().readsetting('httpscertpath')
        if not port:
            port = int(SettingsProvider.get_instance().readsetting('listenporthttps'))
        HTTPServer.__init__(self, ('0.0.0.0', port), handler, )
        SimpleXMLRPCServer.__init__(self, ('0.0.0.0', port), handler, allow_none=True)
        self.socket = ssl.wrap_socket(self.socket, server_side=True, certfile=certFile, keyfile=certFile,
                                      ssl_version=ssl.PROTOCOL_SSLv23)
