#
# Marco Panato
#  2016-03-11
#  Authenticator for frontend
#
#	Each user has a role
#		1 -> min privileges
#		5 -> max privileges

from hashlib import md5
import logging

from database.DataManager import DataManager


class Authenticator(object):

    def authenticate(self, user, password):
        """
            Returns the user's role, or 0 if wrong login occured
        """
        d = DataManager.get_instance().getUsers().get(user.lower())
        if d is not None:
            return d[1] if d[0] == md5(password.encode()).hexdigest() else 0
        return 0

    def adduser(self, user, password, role):
        if role < 1 or role > 5:
            logging.debug('Cannot add role %d!' % role)
            return
        DataManager.get_instance().addUser(user.lower(), password, role)
