from utils.threadedHTTPServer import ThreadedHTTPServer
from utils.urlutils import getUrlPath
from settings.settingsprovider import SettingsProvider
from frontend.songsender import SongSender


class HttpHandler(SongSender):

    def do_GET(self):
        urlPath = getUrlPath(self.path)
        if urlPath[:8] == '/getsong':
            SongSender.handlegetsong(self, 'GET')
        elif urlPath[:4] == "/m3u":
            SongSender.handle_get_playlist(self, 'GET')
        elif urlPath[:8] == "/public/":
            SongSender.handlePublicFolderView(self, urlPath[8:])
        else:
            SongSender.handleerror(self)

    def do_POST(self):
        urlPath = getUrlPath(self.path)
        if urlPath[:8] == '/getsong':
            SongSender.handlegetsong(self, 'POST')
        elif urlPath[:4] == "/m3u":
            SongSender.handle_get_playlist(self, 'POST')
        elif urlPath[:8] == "/public/":
            SongSender.handlePublicFolderView(self, urlPath[8:])
        else:
            SongSender.handleerror(self)


def createHTTPServer():
    server = ThreadedHTTPServer(('0.0.0.0', int(SettingsProvider.get_instance().readsetting('listenporthttp'))),
                                HttpHandler)
    return server
