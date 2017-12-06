PyMusicServer3 - a local music manager with http api and an android application.

https://github.com/Marco9412/MyMusicPlayer2


Requirements (install with pip3):
 - pytaglib     -> python tagging library
 - sqlite3      -> database handler
 - youtube-dl   -> youtube download (downloaded and updated automatically by this server!)
 - defusedxml   -> xmlrpc secure
 - rfc6266      -> header encoding

 Paths:
    /songs/                                     -> main page
    /songs/?type=s                              -> list songs
    /songs/?type=f                              -> root folder
    /songs/?type=f&id=x                         -> list folder with id x
    /songs/?type=p                              -> list playlists
    /songs/?type=p&name=x                       -> list playlist x
    /songs/?type=d&url=u                        -> add song to db from url (youtube only)

    /getsong?id=x                               -> download song with id x
    /getsong?id=0                               -> download a random song

    /m3u?type=folder&ip=x&id=y                  -> m3u file from folderid y
    /m3u?type=folder&ip=x&id=y&rec=y            -> m3u file from foldertree under folderid y
    /m3u?type=playlist&ip=x&name=y              -> m3u file from playlist y

    /public/xxxxxxxxxx                          -> open public url (without credentials on http)

    /songrpc                                    -> rpc path

RPC data:
RPC -> maps of (string -> map)
Song -> map(classname=song, ...)
Folder -> map(classname=folder, ...)
Playlist -> map(classname=playlist, ...)

Features to implement:
 - auto restart server??
 - remove db???

 - localtunnel!

 - autoinstall required libraries!

 - library netbeans -> throw unauthorizedexception!
 - dropbox api -> store server ip
	or other implementation!
 - upnp api -> open ports
 - multiple songs in path
 - gcm in app android to comm IP!
 - writer in settings (create empty file, save new settings, dropbox token)
 - http(s) frontend -> log requests! change format
 - get playlist!
