import threading
import sqlite3
import os
import logging
# import pkg_resources

from music.tagger.tagger import getTags
from settings.settingsprovider import SettingsProvider
from utils.threadingutils import runinanotherthread

# Valid song files
EXTENSIONS = ['.mp3', '.wma', '.wav', '.aac', '.flac', '.aa3']  # TODO .m4a!

MUTEX = threading.Semaphore()  # Mutex

DB_CREATE_SCRIPT = \
    """
--- Folder (name, rowid of the parent folder, isroot)
--- Rootfolder ('/.../.../path', 0, 1)
--- NonRootFolder  ('Marzo', 23, 0)
CREATE TABLE Folder (
    name TEXT NOT NULL,
    parent INTEGER REFERENCES Folder(rowid),
    isroot INTEGER DEFAULT 0,
    PRIMARY KEY (name, parent)
);

CREATE TABLE Song (
    name TEXT NOT NULL,
	folder INTEGER NOT NULL REFERENCES Folder(rowid),
	title TEXT,
	artist TEXT,
	PRIMARY KEY (name, folder)
);

CREATE TABLE Playlist (
	name TEXT,
	song INTEGER REFERENCES Song(rowid),
	PRIMARY KEY (name, song)
);

CREATE TABLE YtVids (
    videoId TEXT PRIMARY KEY,
    songId INTEGER NOT NULL REFERENCES Song(rowid)
);
    """


# ------------------------------------------------------------------------------
# Inserts a folder into database
# ------------------------------------------------------------------------------
def insertFolderDb(conn, name, parent, isroot):
    lastid = -1
    c = conn.cursor()

    # may it exists already?
    c.execute('SELECT rowid FROM Folder WHERE name = ? AND parent = ? AND isroot = ?', [name, parent, isroot])
    row = c.fetchone()
    if row is not None:
        lastid = row[0]
    else:
        c.execute('INSERT INTO Folder VALUES(?,?,?)', [name, parent, isroot])
        lastid = c.lastrowid

    c.close()

    if lastid == -1:
        logging.error('[DBBUILDER] Cannot insert Folder %s, %d, %d' % (name, parent, isroot))

    return lastid


# ------------------------------------------------------------------------------
# Inserts a song into database
# ------------------------------------------------------------------------------
def insertSongDb(conn, name, folder, title=None, artist=None):
    lastid = -1
    c = conn.cursor()

    # may it exists already?
    c.execute('SELECT rowid FROM Song WHERE name = ? AND folder = ?', [name, folder])
    row = c.fetchone()
    if row is not None:
        lastid = row[0]
    else:
        c.execute('INSERT INTO Song VALUES(?,?,?,?)', [name, folder, title, artist])
        lastid = c.lastrowid

    c.close()

    if lastid == -1:
        logging.error('[DBBUILDER] Cannot insert Song %s, %d' % (name, folder))
    return lastid


# ------------------------------------------------------------------------------
# Tells if a song already exists into db
# ------------------------------------------------------------------------------	
def songExistsDb(conn, name, folder):
    c = conn.cursor()
    c.execute('SELECT rowid, name, title, artist FROM Song WHERE name = ? AND folder = ?', [name, folder])
    row = c.fetchone()
    result = row if row is not None else None
    c.close()
    return result


# ------------------------------------------------------------------------------
# Updates metadata for an existent song
# ------------------------------------------------------------------------------
# def updateMetadataSongDb(conn, songid, title, artist):
#    c = conn.cursor()
#    c.execute('UPDATE Song SET title = ?, artist = ? WHERE rowid = ?', [title, artist, songid])

# ------------------------------------------------------------------------------
# Creates the tables into database
# ------------------------------------------------------------------------------
def createDb(conn):
    c = conn.cursor()
    c.execute('SELECT type FROM sqlite_master WHERE type=\'table\' AND name=\'Folder\'')
    row = c.fetchone()
    if row is None:
        c.executescript(DB_CREATE_SCRIPT)
    c.close()


# ------------------------------------------------------------------------------
# Checks if all songs and folders into database exists
# ------------------------------------------------------------------------------
def checkDatabase(conn):
    rootf = []

    c = conn.cursor()
    c.execute('SELECT rowid, name FROM Folder WHERE isroot = 1')
    for row in c:
        rootf.append((row[0], row[1]))

    for f in rootf:
        checkRootFolder(conn, f[0], f[1])
    c.close()


# ------------------------------------------------------------------------------
# Checks if database is consistente this root folder's subtree
# ------------------------------------------------------------------------------
def checkRootFolder(conn, folderid, path):
    if not os.path.isdir(path):
        deleteFolder(folderid)
        return

    c = conn.cursor()
    c.execute('SELECT rowid, name FROM Folder WHERE parent = ?', [folderid])
    for row in c:
        checkFolder(conn, row[0], path + '/' + row[1])


# ------------------------------------------------------------------------------
# Checks if database is consistent for this folder's subtree
# ------------------------------------------------------------------------------
def checkFolder(conn, folderid, path):
    songs = []
    subfolders = []

    if not os.path.isdir(path):
        logging.debug('Folder %s not found! Removing...' % (path))
        deleteFolder(conn, folderid)
        return

    # get songs
    c = conn.cursor()
    c.execute('SELECT rowid, name FROM Song WHERE folder = ?', [folderid])
    for row in c:
        songs.append((row[0], row[1]))

    # check songs
    for song in songs:
        if not os.path.isfile(path + '/' + song[1]):
            logging.debug('[DBBUILDER] Song %s not found! Removing...' % (path + '/' + song[1]))
            deleteSong(conn, song[0])

    # get subfolders
    c.execute('SELECT rowid, name FROM Folder WHERE parent = ?', [folderid])
    for row in c:
        subfolders.append((row[0], row[1]))

    # check subfolders
    for folder in subfolders:
        checkFolder(conn, folder[0], path + '/' + folder[1])

    c.close()


# ------------------------------------------------------------------------------
# Deletes a single song from database
# ------------------------------------------------------------------------------
def deleteSong(conn, songid):
    c = conn.cursor()
    c.execute('DELETE FROM Song WHERE rowid = ?', [songid])
    c.execute('DELETE FROM YtVids WHERE songId = ?', [songid])  # can now re-download yt song!
    c.close()


# ------------------------------------------------------------------------------
# Deletes a folder and its subtree from database
# ------------------------------------------------------------------------------
def deleteFolder(conn, folderid):
    c = conn.cursor()

    # deleting songs
    c.execute('SELECT rowid FROM Song WHERE folder = ?', [folderid])
    for row in c:
        deleteSong(conn, row[0])

    # deleting subfolders
    c.execute('SELECT rowid FROM Folder WHERE parent = ?', [folderid])
    for row in c:
        deleteFolder(conn, row[0])
    # deleting folder
    c.execute('DELETE FROM Folder WHERE rowid = ?', [folderid])

    c.close()


# ------------------------------------------------------------------------------
# Creates song database using basePath as root folder, on dbFile sqlite3 db
#
# 	basePath -> 	/shared/Musica <-- WITHOUT FINAL /
# 	rootFolder -> 	/shared/
# 	First folder -> /shared/Musica
# ------------------------------------------------------------------------------
def buildDb(basePath=None, dbFile=None, async=False):
    if not basePath:
        basePath = str(SettingsProvider.get_instance().read_setting('songbasepath'))
    if not dbFile:
        dbFile = SettingsProvider.get_instance().read_setting('dbfile')

    MUTEX.acquire()

    logging.debug('[DBBUILDER] Building %s database from %s...' % (dbFile, basePath))

    # Fix for path ending with /
    if basePath[-1:] == '/':
        basePath = basePath[:-1]

    conn = sqlite3.connect(dbFile)

    createDb(conn)
    conn.commit()

    # Run in another thread?
    if async:
        conn.close()
        runinanotherthread(buildDbAux, (basePath, dbFile))
    else:
        buildDbAux(basePath, dbFile, conn)


def buildDbAux(basePath, dbFile, conn=None):
    if not conn:
        conn = sqlite3.connect(dbFile)

    i = addRootFolder(conn, basePath[:basePath.rindex('/') + 1])
    addFolder(conn, basePath, i)

    logging.debug('[DBBUILDER] Checking database data...')
    checkDatabase(conn)

    logging.debug('[DBBUILDER] Saving DB to file!')
    conn.commit()
    conn.close()
    logging.debug('[DBBUILDER] All Done')

    MUTEX.release()


# ------------------------------------------------------------------------------
# Extracts song's metadata and adds it to database
# ------------------------------------------------------------------------------
def addSong(conn, name, folder):  # , updatetags = False): # enable elif section!
    title = None
    artist = None

    sid = songExistsDb(conn, os.path.basename(name), folder)
    # sid = (rowid, name, title, artist)
    if sid is None:
        ta = getTags(name)
        if ta is not None:
            title = ta[0]
            artist = ta[1]
        return insertSongDb(conn, os.path.basename(name), folder, title, artist)
    # elif sid[2] != title or sid[3] != artist:
    #    updateMetadataSongDb(conn, sid[0], title, artist)
    return sid[0]


# ------------------------------------------------------------------------------
# Inserts root folder into database
# ------------------------------------------------------------------------------
def addRootFolder(conn, basePath):
    # parent is 0, is root folder
    return insertFolderDb(conn, basePath, 0, 1)


# ------------------------------------------------------------------------------
# Parses a folder and adds it's subtree to database
# ------------------------------------------------------------------------------
def addFolder(conn, path, parent):
    d = []  # folders in folder
    s = []  # songs in folder

    cur = os.listdir(path)
    if len(cur) == 0: return  # do not add empty folders
    for fil in cur:
        if len(fil) > 0 and fil[0] == '.': continue  # Skip hidden files
        if os.path.isfile(path + '/' + fil) and os.path.splitext(fil)[1] in EXTENSIONS:
            # is a song
            s.append(path + '/' + fil)
        if os.path.isdir(path + '/' + fil):
            # is a directory
            d.append(path + '/' + fil)

    # insert current folder
    fid = insertFolderDb(conn, os.path.basename(path), parent, 0)

    # add local songs
    for song in s:
        addSong(conn, song, fid)

    # add sub-dirs
    for folder in d:
        addFolder(conn, folder, fid)
