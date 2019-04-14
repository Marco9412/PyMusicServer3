#
# Url utils
#

import urllib
import urllib.parse
import re


def getUrlPath(url):
    return urllib.parse.urlparse(url).path


def getQueryStringMap(url):
    q = urllib.parse.urlparse(url)
    return urllib.parse.parse_qs(q.query)


def getSongIdFromMap(mapp):
    return -1 if mapp.get('id') is None else int(mapp.get('id')[0])


def getSongIdFromUrl(url):
    return getSongIdFromMap(getQueryStringMap(url))


def checkHostname(url, hostname):
    return urllib.parse.urlparse(url).hostname == hostname


def removeDoubleSlash(str):
    return str.replace('//', '/')


def removeLastSlash(str):
    return str[:-1] if str[-1:] == '/' else str


def getYtVideoId(url):
    u = urllib.parse.urlparse(url)
    h = u.netloc
    if (h == 'www.youtube.com' or h == 'music.youtube.com') and u.path == '/watch':
        qs = urllib.parse.parse_qs(u.query)
        return qs.get('v')[0] if 'v' in qs else None
    if h == 'youtu.be':
        return u.path[1:]
    return None


def fixVideoName(name):
    if '|' in name:
        name = name.replace('|','')
    if '/' in name:
        name = name.replace('/','')

    # TODO other fixes?

    return name


def fixYtSongNameRegex(name):
    exp = re.compile('^(.*)\(.*[oO]fficial.*[vV]ideo.*\)(.*)$', re.I)
    s = exp.search(name)
    if not s: return name # Doesn't match! Nothing to do
    return s.groups()[0] + s.groups()[1] # Two capture groups

