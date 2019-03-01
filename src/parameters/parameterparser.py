import argparse
import logging
import globals

from settings.settingsprovider import new_settings_file
from utils.logging_utils import init_logging
# from utils.printer import redirect_output
# from utils.debugUtils import enable_debug


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--settingsfile', type=str, help='the settings file to use', default='settings.cfg')
    # parser.add_argument('-d', '--debug', action='store_true', help='enable debug mode')
    # parser.add_argument('-r', '--redirect', type=str, metavar='F', help='redirect output to F')
    parser.add_argument('-l', '--log_level', type=str, default='info', choices=['info', 'debug', 'warning'],
                        help='The level of logging required, default info')
    parser.add_argument('-f', '--logstdout', action='store_true', help='Log to stdout')
    parser.add_argument('-v', '--version', action='store_true', help='show version')

    params = parser.parse_args()

    if params.version:
        print('Version: {}, Build date: {}'.format(globals.REVISION, globals.DATE))
        exit(0)

    init_logging(params.log_level, True if params.logstdout else False)

    if params.settingsfile:
        new_settings_file(params.settingsfile)
        logging.info('[PARAMETERPARSER] New settings file is %s' % params.settingsfile)