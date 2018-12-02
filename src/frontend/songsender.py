from cgi import parse_header, FieldStorage
from os.path import isfile, getsize, basename
from shutil import copyfileobj
from mimetypes import guess_type
from http.server import BaseHTTPRequestHandler

import rfc6266
import logging
import urllib
import urllib.parse
import urllib.request

from frontend.webpagebuilder.webresponsebuilder import WebResponseBuilder
from music.manager import PyMusicManager
from utils.urlutils import getSongIdFromMap, getSongIdFromUrl, getQueryStringMap, getUrlPath


class SongSender(BaseHTTPRequestHandler):

    def handleerror(self):
        logging.debug("[HTTPSSERVER] Wrong url")
        self.send_response(404)
        self.end_headers()

    def handle_get_playlist(self, request_type):
        params = getQueryStringMap(self.path) if request_type == 'GET' else self.getpostvariables()

        if params is None:
            self.handleerror()
            return

        ip = params.get('ip')
        if ip:
            ip = ip[0]

        req_type = params.get('type')
        if req_type:
            req_type = req_type[0]

        if req_type == 'folder':
            fol_id = params.get('id')
            if fol_id:
                fol_id = int(fol_id[0])

            rec = params.get('rec')
            if rec:
                rec = True
            else:
                rec = False

            self._sendm3u(PyMusicManager.get_instance().getm3ufromfolder(fol_id, ip, rec), 'plf_%d.m3u' % fol_id)
        elif req_type == 'playlist':
            name = params.get('name')
            if name:
                name = name[0]
            self._sendm3u(PyMusicManager.get_instance().getm3ufromplaylist(name, ip), 'plp_%s.m3u' % name)
        else:
            self.handleerror()

    def getpostvariables(self):
        ctype, pdict = parse_header(self.headers.get_all('content-type')[0])
        if ctype == 'multipart/form-data':

            # Fix! -> parse_multipart with boundary requires bytes!
            pdict2 = {}
            for k, v in pdict.items():
                if isinstance(v, str):
                    pdict2[k] = v.encode()
                else:
                    pdict2[k] = v

            environ = {
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': ctype,
                'CONTENT_LENGTH': self.headers.get_all('content-length')[0]
            }

            return FieldStorage(fp=self.rfile, environ=environ, headers=self.headers)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.get_all('content-length')[0])
            return urllib.parse.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            return {}

    def handlegetsong(self, request_type):
        logging.debug("[HTTPSSERVER] Handling getsong")

        # Get song id
        if request_type == 'GET':
            s_id = getSongIdFromUrl(self.path)
        else:  # POST
            s_id = getSongIdFromMap(self.getpostvariables())

        self._sendsong(s_id)

    def handlePublicFolderView(self, publicurl):
        toSend = WebResponseBuilder(getUrlPath(self.path), 'GET', 1, {'puburl':publicurl, 'type':['publicFol']}).getResponse()
        if toSend:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-length", len(toSend))
            self.end_headers()
            self.wfile.write(toSend)
        else:
            self.send_error(500)

    def _getsongbytesbound(self, size):
        start_range = 0
        end_range = size
        if "Range" in self.headers:
            s, e = self.headers['range'][6:].split('-', 1)
            sl = len(s)
            el = len(e)
            if sl > 0:
                start_range = int(s)
                if el > 0:
                    end_range = int(e) + 1
            elif el > 0:
                ei = int(e)
                if ei < size:
                    start_range = size - ei
        return start_range, end_range

    def _sendsong(self, songid):
        smanager = PyMusicManager.get_instance()
        if songid == 0:
            songid = smanager.getrandomsongid()

        path = smanager.getsongpath(songid)
        if path is not None and isfile(path):
            # open file
            try:
                with open(path, 'rb') as fd:
                    size = getsize(path)
                    filename_header = rfc6266.build_header(basename(path), 'inline')  # Fix for encoding!
                    self.send_response(206 if "Range" in self.headers else 200)
                    self.send_header("Content-type", guess_type(path)[0])
                    self.send_header("Pragma", 'public')
                    self.send_header('Expires', '-1')
                    self.send_header('Cache-Control', 'public, must-revalidate, post-check=0, pre-check=0')
                    self.send_header('Content-Disposition', filename_header)
                    self.send_header('Content-Transfer-Encoding', 'binary')
                    self.send_header('Accept-Ranges', 'bytes')

                    if "Range" in self.headers:
                        d = self._getsongbytesbound(size)
                        # logging.debug("[HTTPSERVER] Range headers: %s, start: %d, end: %d" %
                        # (self.headers['Range'], d[0], d[1]))
                        start_range = d[0]
                        end_range = d[1]
                        self.send_header("Content-Range", 'bytes ' + str(start_range) + '-' + str(end_range - 1) + '/' + str(size))
                        self.send_header("Content-Length", end_range - start_range)
                        # self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                        self.end_headers()

                        size = end_range - start_range
                        fd.seek(start_range) # discard first bytes
                    else:
                        self.send_header("Content-length", size)

                    self.end_headers()
                    copyfileobj(fd, self.wfile, size)  # Send file
            except ConnectionResetError as cre:
                pass
        else:
            self.send_error(500)

    def _sendm3u(self, m3utext, name):
        self.send_response(200)
        self.send_header('Content-type', 'audio/mpegurl')
        self.send_header('Content-length', len(m3utext))
        self.send_header('Content-Disposition', 'attachment; filename=\"' + name + '\"')
        self.end_headers()
        self.wfile.write(m3utext.encode())

    def log_message(self, format, *args):
        logging.debug("%s - - [%s] %s\n" %
                      (self.address_string(),
                       self.log_date_time_string(),
                       format % args))