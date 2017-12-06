#
# Threading utils!
#

import threading


def runinanotherthread(fun, args=(), name=None):
    """ Starts another thread and returns its pointer.
        The thread will be called 'name', and it will execute fun(args).
    """
    t = threading.Thread(target=fun, args=args, name=name)
    t.start()
    return t
