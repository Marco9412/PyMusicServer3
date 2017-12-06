from music.download import downloadMutex
from utils.threadingutils import runinanotherthread

import time
import subprocess
import logging


class YoutubeDlUpdater(object):

    def __init__(self):
        self._goover = False
        self._thread = None

    def _doWork(self):
        while True:
            downloadMutex.acquire()
            logging.debug('[YOUTUBE-DL-UPDATER] Updating youtube-dl library')
            subprocess.call(['/usr/bin/env', 'pip3', 'install', '--user', '--upgrade', 'youtube-dl'])
            downloadMutex.release()

            for i in range(5760):  # Check every day!
                if self._goover:
                    time.sleep(15)
                else:
                    return

    def start(self):
        if self._goover:
            return
        self._goover = True
        self._thread = runinanotherthread(self._doWork)

    def stop(self):
        self._goover = False
        self._thread.join(20)
