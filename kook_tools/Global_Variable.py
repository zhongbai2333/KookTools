global all_variable


def init():
    global all_variable
    all_variable = {}


def set_variable(key, value):
    global all_variable
    all_variable[key] = value


def get_variable(key):
    global all_variable
    if key in all_variable.keys():
        return all_variable[key]
    else:
        return None
