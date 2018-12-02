#
# WebResponseBuilder class
#
# This class handles http connections, building the
# correct HTML webpage
#

from frontend.webpagebuilder.htmlutils import *
from music.manager import PyMusicManager
from settings.settingsprovider import SettingsProvider


class WebResponseBuilder(object):
    def __init__(self, path, requestType, userrole=1, reqvars={}):
        # DEBUG_PRINT('[WEBRESPBUILDER] Creating obj with %s, %s, %d, %s' % (path, requestType, userrole, str(reqvars)))
        # huge output when uploading files
        self._path = path
        self._reqType = requestType
        self._reqvars = reqvars
        self._role = userrole
        self._response = None
        self._buildResponse()

    def getResponse(self):
        return self._response.encode() if self._response else None

    # When using POST and dict, keys and values are stored as bytes!
    # When using GET and dict, keys and values are strings!
    # When using POST and FieldStorage, keys are strings, values are bytes!

    def _readKey(self, key):
        if isinstance(self._reqvars, dict):
            if isinstance(key, str) and self._reqType == 'POST': key = key.encode()
            data = self._reqvars.get(key)
            if data:
                if self._reqType == 'POST':
                    return data[0].decode()
                else:
                    return data[0]
        else:
            # FieldStorage
            return self._reqvars.getvalue(key)

        return None

    def _hasKey(self, key):
        if isinstance(self._reqvars, dict):
            if isinstance(key, str) and self._reqType == 'POST':
                key = key.encode()
            return key in self._reqvars
        else:
            # FieldStorage
            return self._reqvars.getvalue(key)  # TODO not checked!

    def _buildResponse(self):
        type = self._readKey('type')

        if type == 'song':
            self._handleSongsView()

        elif type == 'folder':
            if self._hasKey('id'):
                self._handleFolderView(int(self._readKey('id')))
            else:
                self._handleFolderView(1)

        elif type == 'playlist':
            if self._hasKey('name'):
                self._handlePlaylistView(self._readKey('name'))
            else:
                self._handlePlaylistsView()

        elif type == 'search':
            if self._hasKey('query'):
                self._handlesearchview(self._readKey('query'))
            else:
                self._handleError()

        elif type == 'download':
            if self._hasKey('url') and self._role == 5:
                self._handleDownloadView(self._readKey('url'))
            else:
                self._handleError()

        elif type == 'update':
            if self._role == 5:
                self._handleUpdateView()
            else:
                self._handleError()

        elif type == 'randomsong':
            self._handleRandomSongView()

        elif type == 'upload':
            name = self._reqvars['datafile'].filename
            data = self._reqvars['datafile'].file.read()
            self._handleUploadView(name, data)

        elif type == 'publicFol':
            self._handlePublicUrlView(self._reqvars['puburl'])

        else:
            self._handleMainView()

    def _handlePublicUrlView(self, publicUrl):
        manager = PyMusicManager.get_instance()
        self._handleFolderView(manager.getFolderIdFromPublicUrl(publicUrl), True)

    def _handleFolderView(self, folderid, public=False):
        manager = PyMusicManager.get_instance()
        folder = manager.getfolder(folderid)

        res = writehtmlheader() + writehtmlhead('Folder View')
        if not public:
            res += writehostnamefolderfunction(folderid)
            res += writehostnamefolderfunction(folderid, True)
            res += '<h2>Folder: ' + (
                str(folder.name) if folder.parentId != 0 else 'Root') + '</h2>'

        if folder is not None:
            (s, f) = manager.listfolder(folderid)

            # Write folders
            if not public:
                res += writetableheader(['Name'])
                # Switch to parent
                if folder.parentId != 0:
                    res += (writetablerow(['<a href=\"?type=folder&id=%d\">..</a>' % folder.parentId]))

                if f != []:
                    for fid in f:
                        res += (writetablerow(['<a href=\"?type=folder&id=%d\">%s</a>' % (fid.oid, fid.name)]))
                    res += (writetableend())

            # Write songs
            if s:
                # res += u'<h3>Songs</h3>'
                res += writetableheader(['Title', 'Artist', 'Name'])
                for song in s:
                    res += (writetablerow(
                        [song.title, song.artist, '<a href=\"/%sgetsong?id=%d\">%s</a>' %
                         (SettingsProvider.get_instance().read_setting('redirectbasepath'), song.oid, song.name)]))
                res += (writetableend())

            if not public:
                res += writePublicUrlFunction(folder.getPublicUrl())
                res += '<a href="javascript:void(0)" onClick="moveToPublic();">Public link</a><br>'

        if not public:
            res += '<a href="javascript:void(0)" onClick="getFol();">Get m3u file</a><br>'
            res += '<a href="javascript:void(0)" onClick="getFolR();">Get m3u file for all songs!</a>'

        res += writehtmlend()
        self._response = res

    def _handleSongsView(self):
        manager = PyMusicManager.get_instance()
        songs = manager.listsongsorderedbyname()

        res = writehtmlheader() + writehtmlhead('Song View') + '<h2>Songs</h2>' + writetableheader(
            ['Title', 'Artist', 'Name'])
        for sid in songs:
            res += (writetablerow([sid.title, sid.artist, '<a href=\"/%sgetsong?id=%d\">%s</a>' %
                                   (SettingsProvider.get_instance().read_setting('redirectbasepath'),
                                    sid.oid, sid.name)]))
        res += (writetableend())

        res += writehtmlend()
        self._response = res

    def _handleMainView(self):
        res = writehtmlheader() + writehtmlhead('Main View')
        res += '<a href=\"?type=song\">View songs</a><br>'
        res += '<a href=\"?type=folder\">View folders</a><br>'
        res += '<a href=\"?type=playlist\">View Playlists</a><br>'
        res += '<a href=\"?type=randomsong\">Listen a random song</a><br>'
        res += writesearchform()

        if self._role == 5:
            res += writedownloadform()
            res += writeUploadForm()
            res += '<br><a href=\"?type=update\">Update collection</a><br>'

        res += writehtmlend()
        self._response = res

    def _handleRandomSongView(self):
        manager = PyMusicManager.get_instance()
        sid = manager.getrandomsongid()
        songitem = manager.getsong(sid)

        res = writehtmlheader() + writehtmlhead('Random song')
        res += '<h3>Random song</h3><p>Title ' + songitem.title + '</p><p>Artist: ' + songitem.artist + '</p>'
        res += '<embed src="/' + SettingsProvider.get_instance().read_setting('redirectbasepath') + 'getsong?id=' + \
               str(sid) + '"/>'

        res += writehtmlend()
        self._response = res

    def _handleError(self):
        res = writehtmlheader() + writehtmlhead('Error View')
        res += '<h2>Wrong url!</h2><p><a href=\"/songs/\">Home</a></p>'
        res += writehtmlend()
        self._response = res

    def _handlePlaylistView(self, playlistName):
        """ Shows a playlist """
        manager = PyMusicManager.get_instance()
        playlist = manager.getPlaylists().get(playlistName)

        res = writehtmlheader()

        if playlist is None:
            res += writehtmlhead('Playlist not found') + '<h3>Playlist not found</h3>' + writehtmlend()
        else:
            res += writehtmlhead('Playlist view')
            res += writehostnameplaylistfunction(playlistName)
            res += '<h2>' + playlist.name + '</h2>' + writetableheader(['P'])
            for sid in playlist.songs:
                song = manager.getsong(sid)
                if song is not None:
                    res += (writetablerow(['<a href=\"/%sgetsong?id=%d\">%s</a>' %
                                           (SettingsProvider.get_instance().read_setting('redirectbasepath'),
                                            song.oid, song.name)]))
        res += (writetableend())

        res += '<a href="javascript:void(0)" onClick="getPl();">Get m3u file</a>'

        res += writehtmlend()
        self._response = res

    def _handlePlaylistsView(self):
        """ Shows playlists """
        manager = PyMusicManager.get_instance()
        res = writehtmlheader() + writehtmlhead('Playlists') + '<h2>Playlists</h2>' + writetableheader(['Playlist'])
        for n in manager.listplaylists():
            res += writetablerow(['<a href=\"?type=playlist&name=%s\">%s</a>' % (n, n)])
        res += writetableend()
        res += writehtmlend()

        self._response = res

    def _handlesearchview(self, data):
        manager = PyMusicManager.get_instance()
        res = writehtmlheader() + writehtmlhead('Search results') + '<h2>Search results</h2>'

        res += writetableheader(['Title', 'Artist', 'Name'])
        ss = manager.searchsong(data)
        for s in ss:
            res += writetablerow([s.title, s.artist, '<a href=\"/%sgetsong?id=%d\">%s</a>' %
                                  (SettingsProvider.get_instance().read_setting('redirectbasepath'), s.oid, s.name)])

        res += writetableheader(['Name'])
        ss = manager.searchfolder(data)
        for s in ss:
            res += writetablerow(['<a href=\"?type=folder&id=%d\">%s</a>' % (s.oid, s.name)])

        res += writetableheader(['Name'])
        ss = manager.searchplaylist(data)
        for s in ss:
            res += writetablerow(['<a href=\"?type=playlist&name=%s\">%s</a>' % (s, s)])

        res += writetableend() + writehtmlend()

        self._response = res

    def _handleDownloadView(self, url):
        if self._role < 5:
            self._response = "Forbidden!"
            return

        manager = PyMusicManager.get_instance()

        res = writehtmlheader() + writehtmlhead('Download') + '<h3>Download</h3>'

        if manager.downloadsong(url):
            res += '<p>Song is downloading...</p>'
        else:
            res += '<p>Cannot download song! Server error</p>'
        res += '<br><a href=\"/%ssongs/\">Back</a>' % SettingsProvider.get_instance().read_setting('redirectbasepath')

        res += writehtmlend()

        self._response = res

    def _handleUpdateView(self):
        if self._role < 5:
            self._response = "Forbidden!"
            return

        manager = PyMusicManager.get_instance()

        manager.updateDb()

        res = writehtmlheader() + writehtmlhead('Update') + '<h3>Updating...</h3>'

        res += '<br><a href=\"/%ssongs/\">Back</a>' % SettingsProvider.get_instance().read_setting('redirectbasepath')

        res += writehtmlend()

        self._response = res

    def _handleUploadView(self, name, data):
        if self._role < 5:
            self._response = "Forbidden!"
            return

        manager = PyMusicManager.get_instance()

        res = writehtmlheader() + writehtmlhead('Upload')

        if manager.addRemoteSong(name, data):
            res += '<h3>Upload succesful</h3>'
            res += '<p>Song %s uploaded!</p>' % name
        else:
            res += '<h3>Upload unsuccesful!</h3>'
            res += '<p>Cannot upload %s!</p>' % name

        res += '<br><a href=\"/%ssongs/\">Back</a>' % SettingsProvider.get_instance().read_setting('redirectbasepath')
        res += writehtmlend()

        self._response = res
