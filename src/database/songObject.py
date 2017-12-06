

class SongObject(object):
    def __init__(self, oid, name):
        self.oid = oid
        self.name = name

    def __hash__(self):
        return self.name.__hash__() + self.oid