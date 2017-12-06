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
        'httpscertpath',
        'listenporthttp',
        'listenporthttps'
    ]

    def __init__(self, settingsfilepath = None):
        global SETTINGS_FILE
        if not settingsfilepath:
            settingsfilepath = SETTINGS_FILE
        else:
            SETTINGS_FILE = settingsfilepath

        self.localsettings = {
            'dbfilename': 'songdb.sqlite',
            'dbfilepath': '/tmp',
            'httpscertpath': './sockcert.pem',
            'listenporthttp': '9998',
            'listenporthttps': '9999'
        }
        self.__loadsettings(settingsfilepath)
        self.__checkSettings()

    def __loadsettings(self, settingsfile):
        logging.debug('[SETTINGS] Loading settings from %s' % settingsfile)
        cp = configparser.RawConfigParser()
        if cp.read(settingsfile) != [settingsfile]:
            logging.debug('[SETTINGS] Cannot load settings file %s!' % settingsfile)
            return

        for setting in cp.items('global'):
            self.localsettings[setting[0]] = setting[1]

        # Add custom param
        self.localsettings['dbfile'] = self.localsettings.get('dbfilepath') + '/' + self.localsettings.get('dbfilename')

    def __checkSettings(self):
        for key in SettingsProvider.parameters:
            if key not in list(self.localsettings.keys()):
                logging.critical('Missing parameters! Minimum set is:' + str(SettingsProvider.parameters))
                exit(1)

    def readsetting(self, key):
        return self.localsettings.get(key)

    def getsettingskeys(self):
        return list(self.localsettings.keys())