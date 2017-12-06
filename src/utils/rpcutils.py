
def intDictToStringDict(dictionary):
    """
    Converts dictionary keys into strings.
    :param dictionary:
    :return:
    """
    result = {}
    for k in dictionary:
        result[str(k)] = dictionary[k]
    return result


def stringDictToIntDict(dictionary):
    """
    Converts dictionary keys into integers; non-integer keys won't be in
    result.
    :param dictionary:
    :return:
    """
    result = {}
    for k in dictionary:
        try:
            result[int(k)] = dictionary[k]
        except ValueError:
            pass
    return result