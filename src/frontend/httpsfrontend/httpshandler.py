
from xmlrpc.server import SimpleXMLRPCRequestHandler
import logging

from frontend.authenticator.authenticator import Authenticator
from frontend.authenticator.headerParser import getCredentials
from frontend.songsender import SongSender
from frontend.webpagebuilder.webresponsebuilder import WebResponseBuilder
from music.manager import PyMusicManager
from utils.secureThreadedXMLRPCHTTPServer import SecureThreadedXMLRPCHTTPServer
from utils.urlutils import getQueryStringMap, getUrlPath


class HttpsHandler(SongSender, SimpleXMLRPCRequestHandler):
    rpc_paths = ('/songrpc',)

    def __handleweb(self, requestType, userrole):
        logging.debug("[HTTPSSERVER] Handling web request")
        reqvars = SongSender.getpostvariables(self) if requestType == 'POST' else getQueryStringMap(self.path)

        toSend = WebResponseBuilder(getUrlPath(self.path), requestType, userrole, reqvars).getResponse()
        if toSend:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-length", len(toSend))
            self.end_headers()
            self.wfile.write(toSend)
        else:
            self.send_error(500)

    # Handles headers and parses authentication
    def checklogindata(self):
        cred = getCredentials(self.headers)
        if cred is None:
            # No auth specified, requesting
            self.do_AUTHHEAD()
            return False
        else:
            # Parsing data
            a = Authenticator()
            # if cred is None:  # TODO useless ?
            #     # No auth still specified, re-requesting
            #     self.do_AUTHHEAD()
            #     return False

            role = a.authenticate(cred[0], cred[1])
            if role > 0:
                # Credentials OK!
                return role
            else:
                # Unauthorized
                self.send_response(401)
                self.end_headers()
                return 0

    # For http basic authentication
    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_HEAD(self):
        # logging.debug("head")
        self.do_GET()

    def do_GET(self):
        self._userrole = self.checklogindata()
        if self._userrole > 0:
            urlPath = getUrlPath(self.path)
            if urlPath in HttpsHandler.rpc_paths:
                return SimpleXMLRPCRequestHandler.do_GET(self)
            if urlPath[:8] == "/getsong":
                SongSender.handlegetsong(self, 'GET')
            elif urlPath[:6] == "/songs":
                self.__handleweb('GET', self._userrole)
            elif urlPath[:4] == "/m3u":
                SongSender.handle_get_playlist(self, 'GET')
            elif urlPath[:8] == "/public/":
                SongSender.handlePublicFolderView(self, urlPath[8:])
            else:
                SongSender.handleerror(self)

    def do_POST(self):
        self._userrole = self.checklogindata()
        if self._userrole > 0:
            urlPath = getUrlPath(self.path)
            if urlPath in HttpsHandler.rpc_paths:
                return SimpleXMLRPCRequestHandler.do_POST(self)
            elif urlPath[:8] == '/getsong':
                SongSender.handlegetsong(self, 'POST')
            elif urlPath[:6] == '/songs':
                self.__handleweb('POST', self._userrole)
            elif urlPath[:4] == "/m3u":
                SongSender.handle_get_playlist(self, 'POST')
            elif urlPath[:8] == "/public/":
                SongSender.handlePublicFolderView(self, urlPath[8:])
            else:
                SongSender.handleerror(self)


def createHTTPSServer():
    server = SecureThreadedXMLRPCHTTPServer(HttpsHandler)
    server.register_instance(PyMusicManager.get_instance())
    # server.register_introspection_functions() # Unsecure!
    return server
