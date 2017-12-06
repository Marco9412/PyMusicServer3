from settings.settingsprovider import SettingsProvider

import datetime
import os


class FolderManager(object):
    monthsstr = [
        "Wrongmonth",
        "01Gennaio",
        "02Febbraio",
        "03Marzo",
        "04Aprile",
        "05Maggio",
        "06Giugno",
        "07Luglio",
        "08Agosto",
        "09Settembre",
        "10Ottobre",
        "11Novembre",
        "12Dicembre"
    ]

    def __init__(self):
        self._path = SettingsProvider.get_instance().readsetting('songbasepath') + '/' + str(datetime.date.today().year) + '/' + FolderManager.monthsstr[datetime.date.today().month]

    def getFolderPath(self):
        self._maybeCreateFolder()
        return self._path

    def _maybeCreateFolder(self):
        # Create year folder
        if not os.path.isdir(os.path.dirname(self._path)):
            os.mkdir(os.path.dirname(self._path))

        # Create month folder
        if not os.path.isdir(self._path):
            os.mkdir(self._path)