#
# Marco Panato
# PyMusicServer
#

import logging
import globals

from time import sleep

from database.sqlite3.dbManager import DbManager
from database.DataManager import DataManager
from music.manager import PyMusicManager
from settings.settingsprovider import SettingsProvider
from utils.threadingutils import runinanotherthread
from frontend.httpfrontend.httphandler import createHTTPServer
from frontend.httpsfrontend.httpshandler import createHTTPSServer
from parameters.parameterparser import parse_arguments
from music.download.youtubedlupdater import YoutubeDlUpdater



def main():
    parse_arguments()

    logging.info('PyMusicServer3 %s Marco Panato - %s' % (globals.REVISION, globals.DATE))

    logging.info('[MAIN] Loading settings')
    SettingsProvider.get_instance()

    logging.info('[MAIN] Initializing DbManager')
    DbManager.get_instance()

    logging.info('[MAIN] Initializing DataManager')
    DataManager.get_instance()

    logging.info('[MAIN] Initializing MusicManager')
    PyMusicManager.get_instance()

    logging.info('[MAIN] Initializing youtube-dl updater')
    ydlupdater = YoutubeDlUpdater()
    ydlupdater.start()

    logging.info('[MAIN] Creating HTTP frontend')
    httpfrontend = createHTTPServer()

    logging.info('[MAIN] Creating HTTPS frontend')
    httpsfrontend = createHTTPSServer()

    logging.info('[MAIN] Waiting for clients on port %s and %s...' % (
        SettingsProvider.get_instance().readsetting('listenporthttp'),
        SettingsProvider.get_instance().readsetting('listenporthttps')))
    threadhttp = runinanotherthread(httpfrontend.serve_forever)
    threadhttps = runinanotherthread(httpsfrontend.serve_forever)

    try:
        while True:
            sleep(500)
    except KeyboardInterrupt:
        logging.info("[MAIN] CTRL-C catched! Closing...")
    finally:
        logging.info("[MAIN] Closing server")
        httpfrontend.shutdown()
        httpsfrontend.shutdown()

        threadhttp.join(2)
        threadhttps.join(2)

        del httpfrontend
        del httpsfrontend

        logging.info('[MAIN] Closing youtube-dl updater')
        ydlupdater.stop()

        logging.info("[MAIN] Closing settings manager")
        SettingsProvider.del_instance()

        logging.info("[MAIN] Closing MusicManager")
        PyMusicManager.del_instance()

        logging.info("[MAIN] Closing DataManager")
        DataManager.del_instance()

        logging.info("[MAIN] Closing DbManager")
        DbManager.del_instance()

    logging.info("[MAIN] Bye")


if __name__ == "__main__":
    main()
