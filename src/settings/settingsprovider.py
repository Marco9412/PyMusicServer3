import configparser
import logging

SETTINGS_FILE = './settings.cfg'


def new_settings_file(path):
    global SETTINGS_FILE
    SETTINGS_FILE = path


class SettingsProvider(object):
    instance = None

    @staticmethod
    def get_instance():
        if not SettingsProvider.instance:
            SettingsProvider.instance = SettingsProvider()
        return SettingsProvider.instance

    @staticmethod
    def del_instance():
        if SettingsProvider.instance:
            del SettingsProvider.instance

    # The MUST have parameters to run application
    parameters = [
        'dbfile',
        'songbasepath',
        'listenporthttp',
        'redirectbasepath'
    ]

    def __init__(self, settingsfilepath=None):
        global SETTINGS_FILE
        if not settingsfilepath:
            settingsfilepath = SETTINGS_FILE
        else:
            SETTINGS_FILE = settingsfilepath

        self.localsettings = {
            'dbfilename': 'songdb.sqlite',
            'dbfilepath': '/tmp',
            'listenporthttp': '9999',
            'redirectbasepath': 'panaapps/pymusicserver3/'
        }
        self._load_settings(settingsfilepath)
        self._check_settings()

    def _load_settings(self, settingsfile):
        logging.debug('[SETTINGS] Loading settings from %s' % settingsfile)
        cp = configparser.RawConfigParser()
        if cp.read(settingsfile) != [settingsfile]:
            logging.debug('[SETTINGS] Cannot load settings file %s!' % settingsfile)
            return

        for setting in cp.items('global'):
            self.localsettings[setting[0]] = setting[1]

        # Add custom param
        self.localsettings['dbfile'] = self.localsettings.get('dbfilepath') + '/' + self.localsettings.get('dbfilename')

        # Fix starting / in basepath redirect! (nginx)
        if 'redirectbasepath' in self.localsettings and \
                self.localsettings['redirectbasepath'] != '' and \
                self.localsettings['redirectbasepath'][0] == '/':
            self.localsettings['redirectbasepath'] = self.localsettings['redirectbasepath'][1:]

    def _check_settings(self):
        for key in SettingsProvider.parameters:
            if key not in list(self.localsettings.keys()):
                logging.critical('Missing parameters! Minimum set is:' + str(SettingsProvider.parameters))
                exit(1)

    def read_setting(self, key):
        return self.localsettings.get(key)

    def get_settings_keys(self):
        return list(self.localsettings.keys())
