import datetime
import os
import xmlrpc.client
import random
import logging

from database.sqlite3.dbManager import DbManager
from music.download.foldermanager import FolderManager
from utils.threadingutils import runinanotherthread

from threading import Semaphore
from operator import attrgetter
from os.path import getsize


class DataManager(object):
    """
    This class will load data from database, and keeps all songs data
    in memory.
    """

    instance = None

    @staticmethod
    def get_instance():
        if not DataManager.instance:
            DataManager.instance = DataManager()
        return DataManager.instance

    @staticmethod
    def del_instance():
        if DataManager.instance:
            del DataManager.instance

        # -----------------------------------------------------------------------------

    def __init__(self):
        random.seed()
        self._db = DbManager.get_instance()
        self._mutex = Semaphore(1)
        self._lastUpdate = datetime.datetime.now()
        self._initData()

    def _initData(self):
        logging.debug('[DATAMANAGER] Loading data from db...')
        self._users = self._db.getusers()  # Users
        self._ytids = self._db.listYtUris()  # Yt videos
        self._songsById = self._db.listsongs()  # Songs by id
        self._foldersById = self._db.listfolders()  # Folders by id
        self._rootfolders = self._db.listrootfolders()  # Root folders by id
        self._foldersPathsById = {}  # Paths of music folders
        self._foldersIdByPublicUrls = {} # publicUrl -> folder
        self._songsOrderedByName = sorted(self._songsById.values(), key=attrgetter('name'))  # Sorted songs
        self._foldersOrderedByName = sorted(self._foldersById.values(), key=attrgetter('name'))  # Sorted folders
        self._songsIntoFolderId = {}  # Songs into a folder
        self._foldersIntoFolderId = {}  # Folders into a folder
        self._playlistsByName = {}  # Playlists by name
        self._playlistsOrderedByName = []  # Sorted playlists

        # Folders
        for k in self._foldersById:
            f = self._foldersById[k]
            self._foldersIdByPublicUrls[f.getPublicUrl()] = k
            if f.isroot:
                self._foldersPathsById[f.oid] = f

        # Build tree!
        for k in self._foldersById:
            fol, son = self._buildFolderTree(k)
            self._foldersIntoFolderId[k] = fol
            self._songsIntoFolderId[k] = son

        for k in self._rootfolders:
            fol, son = self._buildFolderTree(k)
            self._foldersIntoFolderId[k] = fol
            self._songsIntoFolderId[k] = son

        # Fetch playlists
        pln = self._db.listplaylists()
        if pln:
            pln.sort()
            for name in pln:
                curpl = self._db.getplaylist(name)
                self._playlistsByName[name] = curpl
                self._playlistsOrderedByName.append(curpl)

    def _buildFolderTree(self, folderid):
        resf = []  # folders
        ress = []  # songs

        # Folders
        for folder in self._foldersById.values():
            if folder.parentId == folderid:
                resf.append(folder)

        # Songs
        for song in self._songsById.values():
            if song.folder == folderid:
                ress.append(song)

        # Sort
        resf.sort(key=attrgetter('name'))
        ress.sort(key=attrgetter('name'))

        return resf, ress

    # -----------------------------------------------------------------------------

    def updateData(self):
        nowtime = datetime.datetime.now()
        if (nowtime - self._lastUpdate).seconds > 300:
            runinanotherthread(self._updateAux)
        else:
            logging.warning('[DATAMANAGER] Blocking too frequent update request!')

    def _updateAux(self):
        self._lastUpdate = datetime.datetime.now()
        self._db.updateDb(False)
        self._initData()

    # -----------------------------------------------------------------------------

    def addSongFromPath(self, songpath):
        self._mutex.acquire()
        # Get song from db
        sid = self._db.addsongfrompath(songpath)

        # Insert song in data structure
        song = self._db.getsong(sid)
        self._songsById[sid] = song

        # Get parent folder
        if song.folder in self._foldersById:
            # Exists:
            # add song to subtree
            self._songsIntoFolderId[song.folder].append(song)
            self._songsIntoFolderId[song.folder].sort(key=attrgetter('name'))
        else:
            # Not exists:
            # get folder from db
            # add folder in data structure (contains song)
            folder = self._db.getfolder(song.folder)
            if not folder:
                logging.error('Error in DB')
                return
            self._foldersById[folder.oid] = folder
            self._songsIntoFolderId[folder.oid] = [song]
            self._foldersIntoFolderId[folder.oid] = []

            # Find parent folders
            # and add them (contains only a folder)
            fid = folder.parentId
            folderparent = folder
            while fid not in self._foldersById:
                folderparent = self._db.getfolder(fid)
                if not folderparent:
                    logging.error('Error in DB')
                    return
                self._foldersById[folderparent.oid] = folderparent
                self._songsIntoFolderId[folderparent.oid] = []
                self._foldersIntoFolderId[folderparent.oid] = [folder]

                folder = folderparent # Maybe fixed inverting this assignment
                fid = folderparent.parentId

            # Add new folder to existent folder
            self._foldersIntoFolderId[fid].append(folderparent)
            self._foldersIntoFolderId[fid].sort(key=attrgetter('name'))

        # Sort new song and folder
        self._songsOrderedByName = sorted(self._songsById.values(), key=attrgetter('name'))
        self._foldersOrderedByName = sorted(self._foldersById.values(), key=attrgetter('name'))  # Sorted folders

        self._mutex.release()
        return sid

    def listsongs(self):
        """
        :return: a map on songid -> Song
        """
        return self._songsById

    def getrandomsongid(self):
        return random.randint(1, len(self._songsById) - 1)

    def listsongsorderedbyname(self):
        return self._songsOrderedByName

    def listfolders(self):
        return self._foldersById

    def listfoldersorderedbyname(self):
        return self._foldersOrderedByName

    def listrootfolders(self):
        return self._rootfolders

    def listplaylists(self):
        return self._playlistsOrderedByName

    def listfolder(self, folderId):
        """
        Lists files and folders into folderid
        :param folderId: the id of the folder to open
        :return: (songmap, foldermap)
        """
        return self._songsIntoFolderId[folderId], self._foldersIntoFolderId[folderId]

    def listfoldersinto(self, folderid):
        return self._foldersIntoFolderId[folderid]

    def listsongsinto(self, folderid):
        return self._songsIntoFolderId[folderid]

    def getsong(self, songid):
        return self._songsById.get(songid)

    def getfolder(self, folderid):
        return self._foldersById.get(folderid)

    def getFolderIdFromPublicUrl(self, publicUrl):
        if publicUrl in self._foldersIdByPublicUrls:
            return self._foldersIdByPublicUrls[publicUrl]
        return 0 # TODO correct?

    def getPublicUrl(self, folderid):
        if folderid in self._foldersById:
            return self._foldersById.get(folderid).getPublicUrl()
        return "" # TODO correct?

    def getplaylist(self, name):
        return self._playlistsByName.get(name)

    def searchsongname(self, name):
        name = name.lower()
        res = []

        for s in self._songsOrderedByName:
            if name in s.name.lower() or name in s.title.lower() or name in s.artist.lower():
                res.append(s)

        return res

    def searchfoldername(self, name):
        name = name.lower()
        res = []

        for f in self._foldersOrderedByName:
            if name in f.name.lower():
                res.append(f)

        return res

    def searchplaylistname(self, name):
        name = name.lower()
        res = []

        for p in self._playlistsOrderedByName:
            if name in p.name.lower():
                res.append(p)

        return res

    def getsongpath(self, songId):
        """
        Returns the path of the song which has "songId".
        """
        currentSong = self._songsById.get(songId)
        if not currentSong:
            return None

        # Calculate path
        path = currentSong.name
        fol_id = currentSong.folder
        while True:
            parentFolder = self._foldersById.get(fol_id)
            if not parentFolder:
                logging.critical('Data inconsistent!!!')
                return None

            path = parentFolder.name + '/' + path
            fol_id = parentFolder.parentId
            if parentFolder.isroot:
                break

        return path

    def canDownload(self, idd):
        for k in self._ytids:
            if k[0] == idd:
                logging.debug('[DATAMANAGER] Video %s already downloaded!' % idd)
                return False
        logging.debug('[DATAMANAGER] Video %s is new: can download!' % idd)
        return True

    def videoDownloaded(self, idd, songid):
        logging.debug('[DATAMANAGER] Adding yt video %s to downloaded!' % idd)
        self._ytids.append((idd, songid))
        self._db.addYtId(idd, songid)

    def getSongSize(self, songid):
        path = self.getsongpath(songid)
        if path: return getsize(path)
        else: return -1

    def addRemoteSong(self, name, data):
        if not isinstance(data, xmlrpc.client.Binary) and \
                not isinstance(data, bytes):
            logging.debug('[DATAMANAGER] Wrong argument for addRemoteSong %s' % type(data).__name__)
            return False

        if isinstance(data, xmlrpc.client.Binary):
            data = data.data

        songpath = FolderManager().getFolderPath() + '/' + name

        if os.path.isfile(songpath) and os.path.getsize(songpath) == len(data):
            logging.debug('[DATAMANAGER] Remote song %s already exists!' % name)
            return True

        logging.debug('[DATAMANAGER] Saving remote song %s!' % name)
        with open(songpath, 'wb') as fd:
            fd.write(data)
        self.addSongFromPath(songpath)
        return True

    # -----------------------------------------------------------------------------
    #   Users data
    # -----------------------------------------------------------------------------
    def addUser(self, username, password, role):
        self._db.addnewuser(username, password, role)

    def getUsers(self):
        return self._users
        # -----------------------------------------------------------------------------

        # def getfolderpath(self, folderid):
        #     """
        #     Returns the path of this folder
        #     """
        #     path = ''
        #
        #     fol_id = folderid
        #     while True:
        #         current = self.getfolder(fol_id)
        #         if not current:
        #             if fol_id == folderid:
        #                 logging.debug('Folder not found')
        #             else:
        #                 logging.debug('Data inconsistent!!!')
        #             return None
        #         path = current.name + '/' + path
        #         fol_id = current.parentId
        #         if current.isroot:
        #             break
        #
        #     return removeLastSlash(removeDoubleSlash(path))
