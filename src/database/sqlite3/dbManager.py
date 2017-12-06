#
#	Sqlite3 database manager
#

import sqlite3
import os
import logging
from hashlib import md5

from database.song import Song
from database.folder import Folder
from database.playlist import Playlist
from database.sqlite3.builder.dbBuilder import buildDb, insertFolderDb, addSong, MUTEX
from settings.settingsprovider import SettingsProvider
from utils.urlutils import removeDoubleSlash, removeLastSlash


class DbManager(object):
    instance = None

    @staticmethod
    def get_instance():
        if not DbManager.instance:
            DbManager.instance = DbManager()
        return DbManager.instance

    @staticmethod
    def del_instance():
        if DbManager.instance:
            del DbManager.instance

    def __init__(self, dbFile = None, build = True):
        if not dbFile:
            self.__dbFile = SettingsProvider.get_instance().readsetting('dbfile')
        else:
            self.__dbFile = dbFile
        logging.debug('[DBUTILS] Opening db %s' % (self.__dbFile))
        if build:
            buildDb(async=False) # Run in current thread

    def updateDb(self, async = True):
        buildDb(async=async)

    def listsongs(self):
        """
        :return: a map on songid -> Song
        """
        conn = sqlite3.connect(self.__dbFile)
        songs = {}

        cursor = conn.cursor()
        cursor.execute('SELECT rowid, * FROM Song')
        for row in cursor:
            songs[row[0]] = Song(row[0], row[1], row[2], (row[3], row[4]))

        cursor.close()
        conn.close()

        return songs

    def listfolders(self):
        """
        :return: a map on folderid -> folder
        """
        conn = sqlite3.connect(self.__dbFile)
        folders = {}

        cursor = conn.cursor()
        cursor.execute('SELECT rowid, * FROM Folder')
        for row in cursor:
            folders[row[0]] = Folder(row[0], row[1], row[2], row[3])

        cursor.close()
        conn.close()

        return folders

    def listrootfolders(self):
        """
        Lists the root folders of this song db
        :return: a map of folderid -> folder
        """
        conn = sqlite3.connect(self.__dbFile)
        folders = {}
        cursor = conn.cursor()
        c2 = conn.cursor()
        cursor.execute('SELECT rowid FROM Folder WHERE isroot = 1')
        for row in cursor:
            c2.execute('SELECT rowid, name FROM Folder WHERE parent = ?', [row[0]])
            for r in c2:
                folders[r[0]] = (Folder(r[0], r[1], row[0], 0))
        c2.close()
        cursor.close()
        conn.close()
        return folders

    def listplaylists(self):
        """
        :return: a list of playlists names
        """
        conn = sqlite3.connect(self.__dbFile)
        names = []
        c = conn.cursor()
        c.execute('SELECT DISTINCT name FROM Playlist ORDER BY name')
        for row in c:
            names.append(row[0])
        c.close()
        conn.close()
        return names

    def listYtUris(self):
        conn = sqlite3.connect(self.__dbFile)
        ids = []
        c = conn.cursor()
        c.execute('SELECT videoId, songId FROM YtVids')
        for row in c:
            ids.append((row[0], row[1]))
        c.close()
        conn.close()
        return ids

    def getsong(self, songid):
        """
        :return: the Song object with songid
        """
        conn = sqlite3.connect(self.__dbFile)
        song = None

        cursor = conn.cursor()
        cursor.execute('SELECT rowid, * FROM Song WHERE rowid = ?', [songid])
        row = cursor.fetchone()
        if row is not None:
            song = Song(row[0], row[1], row[2], (row[3], row[4]))

        cursor.close()
        conn.close()

        return song

    def getfolder(self, folderid):
        """
        The Folder object with the given id
        """
        res = None

        conn = sqlite3.connect(self.__dbFile)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Folder where rowid = ?', [folderid])
        row = cursor.fetchone()
        if row is not None:
            res = Folder(folderid, row[0], row[1], row[2])
        cursor.close()
        conn.close()

        return res

    def getplaylist(self, name):
        """
        :return: the Playlist object associated with the name
        """
        conn = sqlite3.connect(self.__dbFile)
        playlist = None

        cursor = conn.cursor()
        songs = []
        cursor.execute('SELECT song FROM Playlist WHERE name = ?', [name])
        for row in cursor:
            songs.append(row[0])
        playlist = Playlist(name, songs)

        cursor.close()
        conn.close()

        return playlist

    def addfolderfrompath(self, path):
        """ Returns the folder id into db from a folder path.
            It will insert the folder if it doesn't esists.
        """
        path = removeLastSlash(removeDoubleSlash(path))
        fid = self.__getfolderidfrompath(path)
        if fid is not None:
            return fid

        # Find if path is in one root folder!
        canadd = False
        roots = self._getrootfolderspaths()
        for fol in roots:
            d = roots[fol].name
            if d == path[:len(d)]:
                canadd = True
                break

        return self.__addnewfolderfrompath(path) if canadd else None

    def addsongfrompath(self, path):
        """
            Adds the song pointed by path into database,
            and returns its id.
        """
        if not os.path.isfile(path):
            logging.error('Cannot add a non-esistent file %s' % path)
            return None

        songfolder = path[: path.rindex('/')]

        fid = self.addfolderfrompath(songfolder)
        if fid is None:
            logging.error('Cannot add song in db %s' % path)
            return None

        conn = sqlite3.connect(self.__dbFile)
        MUTEX.acquire()
        sid = addSong(conn, path, fid)
        conn.commit()
        MUTEX.release()
        conn.close()

        return sid

    def getusers(self):
        users = {}
        sq = sqlite3.connect(self.__dbFile)
        c = sq.cursor()
        for row in c.execute('SELECT rowid, name, pass, role FROM User'):
            logging.debug("[DBUTILS] Found user " + row[1])
            users[row[1]] = (row[2], row[3])
        sq.close()

        return users

    def addnewuser(self, username, password, role):
        logging.debug("[DBUTILS] Adding new user (%s,*****, %d)" % (username, role))
        sq = sqlite3.connect(self.__dbFile)
        c = sq.cursor()
        c.execute('INSERT INTO User VALUES(?,?,?)', [username, md5(password.encode()).hexdigest(), role])
        sq.commit()
        sq.close()

    def __addnewfolderfrompath(self, path):
        path = removeLastSlash(removeDoubleSlash(path))
        canadd = False

        parentpath = path[:path.rindex('/')]
        parentid = self.addfolderfrompath(parentpath)
        if parentid is None:
            logging.error('Error while adding %s, %s, %d' % (path, parentpath, parentid))
            return None

        conn = sqlite3.connect(self.__dbFile)
        MUTEX.acquire()
        currid = insertFolderDb(conn, path[path.rindex('/')+1:], parentid, 0)
        conn.commit()
        MUTEX.release()
        conn.close()

        return currid

    def __getfolderidfrompath(self, path):
        """ Returns the folder id into db from a folder path,
            or None if folder isn't into db
        """
        path = removeLastSlash(removeDoubleSlash(path))
        if not os.path.isdir(path): return None

        roots = self._getrootfolderspaths()
        for fol in roots:
            cur = roots[fol]
            fid = self.__getfolderidfrompathaux(cur.name, path, cur.oid)
            if fid is not None: return fid

        # Not found!
        return None

    def __getfolderidfrompathaux(self, basepath, path, fid):
        basepath = removeLastSlash((removeDoubleSlash(basepath)))
        if not os.path.isdir(path): return None

        subs = self._listfoldersinto(fid)
        for fid in subs:
            curr = basepath + '/' + subs[fid].name
            if curr == path:
                return subs[fid].oid
            elif curr == path[:len(curr)]:
                return self.__getfolderidfrompathaux(curr, path, subs[fid].oid)

        return None

    def _listfoldersinto(self, folderid):
        conn = sqlite3.connect(self.__dbFile)
        folders = {}

        cursor = conn.cursor()
        cursor.execute('SELECT rowid, * FROM Folder WHERE parent = ?', [folderid])
        for row in cursor:
            folders[row[0]] = Folder(row[0], row[1], row[2], row[3])

        cursor.close()
        conn.close()

        return folders

    def _getrootfolderspaths(self):
        conn = sqlite3.connect(self.__dbFile)
        folders = {}
        c2 = conn.cursor()

        c2.execute('SELECT rowid, * FROM Folder WHERE isroot = 1')
        for row in c2:
            folders[row[0]] = Folder(row[0], row[1], row[0], 1)

        c2.close()
        conn.close()
        return folders

    def addYtId(self, idd, songid):
        conn = sqlite3.connect(self.__dbFile)
        c = conn.cursor()

        c.execute('INSERT INTO YtVids VALUES (?, ?)', [idd, songid])

        c.close()
        conn.commit()
        conn.close()