
import logging

from xmlrpc.server import SimpleXMLRPCRequestHandler

from utils.ThreadedXMLRPCHTTPServer import ThreadedXMLRPCHTTPServer
from utils.urlutils import getUrlPath, getQueryStringMap
from frontend.songsender import SongSender
from frontend.webpagebuilder.webresponsebuilder import WebResponseBuilder
from music.manager import PyMusicManager


class HttpHandler(SongSender, SimpleXMLRPCRequestHandler):
    rpc_paths = ('/songrpc',)

    def __handleweb(self, requestType, userrole):
        logging.debug("[HTTPSERVER] Handling web request")
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

    def do_HEAD(self):
        # logging.debug("head")
        self.do_GET()

    def do_GET(self):
        urlPath = getUrlPath(self.path)
        if urlPath[:8] == '/getsong':
            SongSender.handlegetsong(self, 'GET')
        elif urlPath[:6] == "/songs":
            self.__handleweb('GET', 5)  # TODO role 5 ? -> authentication done by nginx!
        elif urlPath[:4] == "/m3u":
            SongSender.handle_get_playlist(self, 'GET')
        elif urlPath[:8] == "/public/":
            SongSender.handlePublicFolderView(self, urlPath[8:])
        else:
            SongSender.handleerror(self)

    def do_POST(self):
        urlPath = getUrlPath(self.path)
        if urlPath in HttpHandler.rpc_paths:
            return SimpleXMLRPCRequestHandler.do_POST(self)
        if urlPath[:8] == '/getsong':
            SongSender.handlegetsong(self, 'POST')
        elif urlPath[:6] == "/songs":
            self.__handleweb('GET', 5)  # TODO role 5 ? -> authentication done by nginx!
        elif urlPath[:4] == "/m3u":
            SongSender.handle_get_playlist(self, 'POST')
        elif urlPath[:8] == "/public/":
            SongSender.handlePublicFolderView(self, urlPath[8:])
        else:
            SongSender.handleerror(self)


def create_http_server():
    server = ThreadedXMLRPCHTTPServer(HttpHandler, listen_localhost=True)
    server.register_instance(PyMusicManager.get_instance())
    return server
