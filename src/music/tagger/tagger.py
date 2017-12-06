import taglib
import os
import logging
from utils.urlutils import fixYtSongNameRegex


def getTags(path):
    logging.debug('[TAGGER] Extracting tags from %s' % path)
    try:
        data = taglib.File(path)
        if data is not None and data.tags is not None \
                and 'TITLE' in data.tags and 'ARTIST' in data.tags \
                and data.tags['TITLE'] and data.tags['ARTIST']:
            return data.tags['TITLE'][0], data.tags['ARTIST'][0]
        else:
            name = os.path.basename(path)
            name = name[:name.rindex('.')]
            return extractTagsYoutube(os.path.basename(name))
    except OSError:
        pass
    return None


def extractTagsYoutube(name):
    if '-' not in name:  # wrong video!
        return name, ""

    artist = name[: name.index('-') - 1]  # youtube common names!
    title = fixYtSongNameRegex(name[name.index('-') + 2:])

    logging.debug('[TAGGER] Youtube: %s -> %s,%s' % (name, title,artist))

    return title, artist


def setTags(path, title, artist):
    try:
        data = taglib.File(path)
        data.tags['TITLE'] = [title]
        data.tags['ARTIST'] = [artist]
        data.save()
        return True
    except OSError:
        return False


def setTagsYt(path, vname):
    d = extractTagsYoutube(vname)
    title = d[0]
    artist = d[1]
    return setTags(path, title, artist)
