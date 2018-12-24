from database.DataManager import DataManager
from music.tagger.tagger import setTagsYt
from music.download import downloadMutex
from music.download.foldermanager import FolderManager
from utils.urlutils import checkHostname, getYtVideoId, fixVideoName
from utils.threadingutils import runinanotherthread

import time
import logging
import uuid
import os
import sys


class PyYoutubeDownloader(object):

    def __init__(self, url):
        logging.debug('[DOWNLOADER] Created object with %s' % url)
        self.url = url
        self._videoId = getYtVideoId(url)
        # done in getYtVideoId(url)
        # self.__canrun = checkHostname(url, 'www.youtube.com') or checkHostname(url, 'youtu.be')

        if not self._videoId:
            logging.debug('[DOWNLOADER] Cannot extract ID from this URL!')
            self.__canrun = false
        else:
            self.__canrun = DataManager.get_instance().canDownload(self._videoId)

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

                tmpuuid = uuid.uuid4()
                tmpsong = '{}/{}'.format(outputfolder, str(tmpuuid))

                # Defaults options
                ydloptions = dict(format='bestaudio/best', postprocessors=[
                    dict(key='FFmpegExtractAudio', preferredcodec='mp3', preferredquality='320')
                    # ], outtmpl=outputfolder + '/%(title)s.%(ext)s')
                ], outtmpl=tmpsong + '.%(ext)s')

                logging.debug('[DOWNLOADER] Downloading temporary file %s' % tmpsong)

                # Get media info
                videoinfo = youtube_dl.YoutubeDL(ydloptions).extract_info(self.url)
                videoname = fixVideoName(videoinfo.get('title'))
                logging.debug('[DOWNLOADER] Video name is %s' % videoname)
                if videoname is not None:
                    newsong = outputfolder + '/' + videoname + '.mp3'
                    tmpsong = tmpsong + '.mp3'
                    logging.debug('[DOWNLOADER] Renaming {} to {}'.format(tmpsong, newsong))
                    os.rename(tmpsong, newsong)  # renaming to correct name
                    if not setTagsYt(newsong, videoname):
                        logging.warning("[DOWNLOADER] Cannot set youtube tags to song %s" % newsong)
                    logging.debug('[DOWNLOADER] Adding to database %s' % newsong)
                    songid = DataManager.get_instance().addSongFromPath(newsong)
                    if self._videoId and songid:
                        logging.debug('[DOWNLOADER] Adding video id to database')
                        DataManager.get_instance().videoDownloaded(self._videoId, songid)

                downloadMutex.release()
                return
            except ImportError:
                downloadMutex.release()
                logging.debug('[DOWNLOADER] Youtube-dl module is updating... retrying in 10 seconds...')
                time.sleep(10)
            except:
                downloadMutex.release()
                print('[DOWNLOADER] Download error {}'.format(str(sys.exc_info())))
                return
