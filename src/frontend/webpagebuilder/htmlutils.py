#
# Html utils
#

from settings.settingsprovider import SettingsProvider


def writehtmlheader():
    return "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1" \
           "-transitional.dtd\">\n<html xmlns=\"http://www.w3.org/1999/xhtml\">"


def writehtmlhead(title):
    return '<head>\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" />' \
           '\n<title>{titl}</title>\n</head><body>'.format(titl=title)


def writehtmlend():
    return '</body></html>'


def writetableheader(columns):
    res = '<table border=\"1\"><tr>'
    for c in columns:
        res += ('<th scope=\"col\">%s</th>' % c)
    res += '</tr>'
    return res


def writetablerow(values):
    res = '<tr>'
    for v in values:
        res += '<td align=\"center\">%s</td>' % v
    res += '</tr>'
    return res


def writetableend():
    return '</table>'


def writefieldsetstyle():
    return '<style type="text/css">' \
           '   .fieldset-auto-width {' \
           '       display: inline-block;' \
           '   } </style>'


def writesearchform():
    return writefieldsetstyle() + \
           '<form method = \"get\" action=\"\">' \
           '<fieldset class="fieldset-auto-width">' \
           'Search data<br>' \
           '<input type="hidden" name="type" value="search" />' \
           '<input type="text" name="query"/><input type="submit" value="Search"/>' \
           '</fieldset>' \
           '</form>'
    # u'<input type="radio" name="what" value="song" checked> Song<br>' \
    # u'<input type="radio" name="what" value="folder"> Folder<br>' \
    # u'<input type="radio" name="what" value="playlist"> Playlist<br>' \


def writedownloadform():
    return writefieldsetstyle() + '<form method = \"get\" action=\"\"> ' \
                                  '<fieldset class="fieldset-auto-width">' \
                                  'Add song from youtube: <br>' \
                                  '<input type=\"text\" name=\"url\"/> ' \
                                  '<input type=\"hidden\" name=\"type\" value=\"download\" />' \
                                  '<input type=\"submit\" value=\"Download\" /> ' \
                                  '</fieldset>' \
                                  '</form>'


def writehostnamefolderfunction(idd, rec=False):
    # window.location.href = '...';
    return '<script>' \
           'function getFol%s() {' \
           '  window.location.href="/%sm3u?type=folder&id=%d%s&ip=" + window.location.hostname' \
           '}' \
           '</script>' % ('R' if rec else '', SettingsProvider.get_instance().read_setting('redirectbasepath'),
                          idd, '&rec=y' if rec else '')


def writePublicUrlFunction(url):
    return '<script>' \
           'function moveToPublic() {' \
           '    window.location.href = \'http://\' + window.location.hostname + \'/%spublic/%s\'' \
           '}' \
           '</script>' % (SettingsProvider.get_instance().read_setting('redirectbasepath'), url)


def writehostnameplaylistfunction(name):
    return '<script>' \
           'function getPl() {' \
           '  window.location.href="/%sm3u?type=playlist&name=%s"' \
           '}' \
           '</script>' % (SettingsProvider.get_instance().read_setting('redirectbasepath'), name)


def writeUploadForm():
    return """<form action="" method="post" enctype="multipart/form-data">
                <fieldset class="fieldset-auto-width">
                    <input type="hidden" name="type" value="upload" />
                    <input accept="audio/*" type="file" name="datafile">
                    <input type="submit" value="Upload">
                </fieldset>
               </form>"""
