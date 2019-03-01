
import logging

LOG_FILENAME = 'pymusicserver3.log'


def log_level_string_to_log_level(log_level):
    if log_level == 'info':
        return logging.INFO
    if log_level == 'warning':
        return logging.WARNING
    if log_level == 'debug':
        return logging.DEBUG
    return logging.DEBUG


def save_log_file():
    import os
    if LOG_FILENAME in os.listdir('.'):
        os.rename(LOG_FILENAME, '%s.old' % LOG_FILENAME)


def init_logging(level=logging.INFO, logstdout=False):
    if not logstdout:
        save_log_file()
        logging.basicConfig(format='%(levelname)s\t%(asctime)s\t%(message)s',
                            level=log_level_string_to_log_level(level), filename=LOG_FILENAME, filemode='w')
    else:
        logging.basicConfig(format='%(levelname)s\t%(asctime)s\t%(message)s',
                            level=log_level_string_to_log_level(level))
