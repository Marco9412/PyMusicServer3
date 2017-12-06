from database.songObject import SongObject
from mimetypes import guess_type


class Song(SongObject):

    def __init__(self, oid, name, folder, tags=None):
        SongObject.__init__(self, oid, name)
        self.folder = folder
        self.title = None
        self.artist = None
        if tags is not None:
            self.title = tags[0]
            self.artist = tags[1]
        self.classname = type(self).__name__

    def getMimeType(self):
        type = guess_type(self.name)
        if type:
            return type[0]
        else: return None

    def __str__(self):
        return 'S(%d, %s, %d, %s, %s)' % (self.oid, str(self.name), self.folder, self.title, self.artist)

    __repr__ = __str__
