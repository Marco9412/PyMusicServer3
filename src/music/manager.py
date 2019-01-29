#
# Music manager
#

from database.DataManager import DataManager
from music.download.youtubedownloader import PyYoutubeDownloader
from settings.settingsprovider import SettingsProvider
from utils.rpcutils import intDictToStringDict


class PyMusicManager(object):
    instance = None

    @staticmethod
    def get_instance():
        if not PyMusicManager.instance:
            PyMusicManager.instance = PyMusicManager()
        return PyMusicManager.instance

    @staticmethod
    def del_instance():
        if PyMusicManager.instance:
            del PyMusicManager.instance

    def __init__(self):
        self._dm = DataManager.get_instance()

    def getsongpath(self, songid):
        return self._dm.getsongpath(songid)

    def getsong(self, songid):
        return self._dm.getsong(songid)

    def getrandomsongid(self):
        return self._dm.getrandomsongid()

    def getfolder(self, folderid):
        return self._dm.getfolder(folderid)

    def getFolderIdFromPublicUrl(self, publicUrl):
        return self._dm.getFolderIdFromPublicUrl(publicUrl)

    def getPublicUrl(self, folderid):
        return self._dm.getPublicUrl(folderid)

    def listfolder(self, folderid):
        return self._dm.listfolder(folderid)

    def listsongsinto(self, folderid):
        return self._dm.listsongsinto(folderid)

    def listfoldersinto(self, folderid):
        return self._dm.listfoldersinto(folderid)

    def getrootfolders(self):
        return self._dm.listrootfolders()

    def getrootfoldersrpc(self):
        return list(self.getrootfolders().values())

    def listsongs(self):
        return self._dm.listsongs()

    def listsongsrpc(self):
        return intDictToStringDict(self.listsongs())

    def listsongsorderedbyname(self):
        return self._dm.listsongsorderedbyname()

    def listfolders(self):
        return self._dm.listfolders()

    def listfoldersrpc(self):
        return intDictToStringDict(self.listfolders())

    def listfoldersorderedbyname(self):
        return self._dm.listfoldersorderedbyname()

    def getplaylist(self, name):
        return self._dm.getplaylist(name)

    def listplaylists(self):
        return self._dm.listplaylists()

    def searchsong(self, name):
        return self._dm.searchsongname(name)

    def searchfolder(self, name):
        return self._dm.searchfoldername(name)

    def searchplaylist(self, name):
        return self._dm.searchplaylistname(name)

    def readsong(self, songid):
        """ Returns an array containing the song identified by 'songid'
            and its name
            (data, songname)
        """
        data = None
        path = self.getsongpath(songid)
        song = self.getsong(songid)
        if path is not None:
            with open(path, 'rb') as f:
                data = f.read()
        return data, song.name

    def addRemoteSong(self, name, data):
        return self._dm.addRemoteSong(name, data)

    def downloadsong(self, url):
        PyYoutubeDownloader(url).download()
        return True

    def getm3ufromplaylist(self, name, myremoteip):
        res = '#EXTM3U\n'
        playlist = self._dm.getplaylist(name)
        if not playlist:
            return None
        songs = playlist.songs
        for songid in songs:
            song = self._dm.getsong(songid)
            if song:
                res += '#EXTINF:%d, %s - %s\n' % (song.oid, song.artist, song.title)
            res += 'http://%s:%s/%sgetsong?id=%d\n' % (myremoteip,
                                                       SettingsProvider.get_instance().read_setting('redirectport'),
                                                       SettingsProvider.get_instance().read_setting('redirectbasepath'),
                                                       songid)
        return res

    def getm3ufromfolder(self, folderid, myremoteip, recursive=False, header=True):
        res = '#EXTM3U\n' if header else ''
        songs = self._dm.listsongsinto(folderid)
        for song in songs:
            res += '#EXTINF:%d, %s - %s\n' % (song.oid, song.artist, song.title)
            res += 'http://%s:%s/%sgetsong?id=%d\n' % (myremoteip,
                                                       SettingsProvider.get_instance().read_setting('redirectport'),
                                                       SettingsProvider.get_instance().read_setting('redirectbasepath'),
                                                       song.oid)

        if recursive:
            folders = self._dm.listfoldersinto(folderid)
            for folder in folders:
                res += self.getm3ufromfolder(folder.oid, myremoteip, recursive, header=False)

        return res

    def updateDb(self):  # TODO role?
        self._dm.updateData()

    def getsongsize(self, songid):
        return self._dm.getSongSize(songid)
