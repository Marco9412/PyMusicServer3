from database.DataManager import DataManager
from music.tagger.tagger import setTagsYt
from music.download import downloadMutex
from music.download.foldermanager import FolderManager
from utils.urlutils import checkHostname, getYtVideoId, fixVideoName
from utils.threadingutils import runinanotherthread

import time
import logging


class PyYoutubeDownloader(object):

    def __init__(self, url):
        logging.debug('[DOWNLOADER] Created object with %s' % url)
        self.url = url
        self._videoId = getYtVideoId(url)
        self.__canrun = checkHostname(url, 'www.youtube.com') or checkHostname(url, 'youtu.be')

        if not self._videoId:
            logging.debug('[DOWNLOADER] Cannot extract ID from this URL!')
        else:
            self.__canrun = self.__canrun and DataManager.get_instance().canDownload(self._videoId)

    def download(self):
        if self.__canrun:
            runinanotherthread(self.__downloadSync)

    def __downloadSync(self):
        while True:
            try:
                downloadMutex.acquire()

                import youtube_dl
                import importlib
                importlib.reload(youtube_dl)

                outputfolder = FolderManager().getFolderPath()

                # Defaults options
                ydloptions = dict(format='bestaudio/best', postprocessors=[
                    dict(key='FFmpegExtractAudio', preferredcodec='mp3', preferredquality='320')
                ], outtmpl=outputfolder + '/%(title)s.%(ext)s')

                # Get media info
                videoname = fixVideoName(youtube_dl.YoutubeDL(ydloptions).extract_info(self.url).get('title'))
                logging.debug('[DOWNLOADER] Video name is %s' % videoname)
                if videoname is not None:
                    newsong = outputfolder + '/' + videoname + '.mp3'
                    if not setTagsYt(newsong, videoname):
                        logging.warning("[DOWNLOADER] Cannot set youtube tags to song %s" % newsong)
                    logging.debug('[DOWNLOADER] Adding to database %s' % newsong)
                    songid = DataManager.get_instance().addSongFromPath(newsong)
                    if self._videoId and songid:
                        logging.debug('[DOWNLOADER] Adding video id to database')
                        DataManager.get_instance().videoDownloaded(self._videoId, songid)

                downloadMutex.release()
                return
            except: #import sys  #print("Unexpected error:", sys.exc_info()[0])
                downloadMutex.release()

                logging.debug('[DOWNLOADER] Youtube-dl module is updating or download error... retrying in 10 seconds...')
                time.sleep(10)
