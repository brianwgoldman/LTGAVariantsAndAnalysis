import inspect


def classMethods(classType):
    return dict(inspect.getmembers(classType, inspect.ismethod))
