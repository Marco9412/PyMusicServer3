from database.songObject import SongObject
import hashlib

class Folder(SongObject):

    def __init__(self, oid, name, parentId, isroot, items=None):
        SongObject.__init__(self, oid, name)
        self.parentId = parentId
        self.isroot = isroot == 1
        self.items = items
        self.classname = type(self).__name__

    def hasItems(self):
        return self.items is not None

    def getPublicUrl(self):
        return hashlib.md5((str(self.name) + str(self.oid)).encode(errors='continue')).hexdigest()

    def __str__(self):
        return 'F(%d, %s, %d, %r, %s)' % \
               (self.oid, self.name.encode('utf-8'), self.parentId, self.isroot, str(self.items))

    __repr__ = __str__
