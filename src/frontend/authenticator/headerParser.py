#
# Marco Panato
#  2016-03-11
#  Parser for basic http authentication
#

from base64 import b64decode


def getCredentials(headers):
    if headers is None:
        return None

    data = headers.get('Authorization')
    if data is None: return None  # no auth specified

    (basic, _, encoded) = data.partition(' ')
    if basic != 'Basic': return None  # wrong parameters

    (username, _, password) = str(b64decode(encoded)).partition(':')
    return (username[2:], password[:-1])
