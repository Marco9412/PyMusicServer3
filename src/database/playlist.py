

class Playlist(object):

    def __init__(self, name, songs=[]):
        self.name = name
        self.songs = []
        self.classname = type(self).__name__

    def __str__(self):
        return 'P(%s,%s)' % (self.name, str(self.songs))

    __repr__ = __str__
