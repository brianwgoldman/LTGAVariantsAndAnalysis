'''
Module containing a host of useful functions that do not fall into more
explicit categories.
'''
import inspect
import json
import random
import math
import os
import itertools


def classMethods(classType):
    '''
    Given a class type, return a dictionary mapping string names of that
    class's methods to the actual method.  For instance
    ``classMethod(LTGA)['twoParentCrossover']`` will return the
    ``twoParentCrossover`` function.

    Parameters:

    - ``classType``: Specifies what class to retrieve methods for.
    '''
    return dict(inspect.getmembers(classType, inspect.ismethod))


def moduleClasses(module):
    '''
    Given a module, return a dictionary mapping string names of that
    module's classes to the actual classes.  For instance
    ``moduleClasses(FitnessFunction)['DeceptiveTrap']`` will return the
    ``DeceptiveTrap`` class.

    Parameters:

    - ``module``: Specifies what module to retrieve classes for.
    '''
    return dict(inspect.getmembers(module, inspect.isclass))


def loadConfiguration(filename, fileMethod=open):
    '''
    Loads a json from the given file name.  Optional file method allows for
    compressed files.

    Parameters:

    - ``filename``: The relative path to the file to be loaded.
    - ``fileMethod``: Handler to use to open the file.  Defaults to regular
      open.
    '''
    with fileMethod(filename, 'r') as f:
        return json.load(f)


def loadConfigurations(filenames, fileMethod=open):
    '''
    Given a list of file names, create a single dictionary containing all of
    their contents.  Repeated keywords will override previously encountered
    values.  Optional file method allows for
    compressed files.

    Parameters:

    - ``filenames``: A list of relative paths to the files to be loaded.
    - ``fileMethod``: Handler to use to open the file.  Defaults to regular
      open.
    '''
    result = {}
    for filename in filenames:
        result.update(loadConfiguration(filename, fileMethod))
    return result


def saveConfiguration(filename, data, fileMethod=open):
    '''
    Writes a block of json-able data to the specifed file path.

    Parameters:

    - ``filename``: The relative path to the file to be written to.
    - ``data``: Data that can be converted to a json.  IE dictionaries and
      lists.
    - ``fileMethod``: Handler to use to open the file.  Defaults to regular
      open.
    '''
    with fileMethod(filename, 'w') as f:
        json.dump(data, f)


def saveList(filename, data, fileMethod=open):
    '''
    Write out a list of jsons in a more human readable way than
    ``saveConfiguration``.

    Parameters:

    - ``filename``: The relative path to the file to be written to.
    - ``data``: A list of json-able data to be written
    - ``fileMethod``: Handler to use to open the file.  Defaults to regular
      open.
    '''
    with fileMethod(filename, 'w') as f:
        f.write('[' + os.linesep)
        for lineNumber, line in enumerate(data):
            json.dump(line, f)
            if lineNumber != len(data) - 1:
                f.write(",")
            f.write(os.linesep)
        f.write(']' + os.linesep)


def randomBitString(length):
    '''
    Generate and return a random list of 0s and 1s.

    Parameters:

    - ``length``: The length of the list to be generated.
    '''
    generated = bin(random.getrandbits(length))[2:]  # String of bits
    leadingZeros = '0' * (length - len(generated)) + generated
    return map(int, leadingZeros)


def median(data, default=0):
    '''
    Given a data set, return the median value.

    Parameters:

    - ``data``: The data to find the median of.
    - ``default``: If ``data`` contains no information, what value should be
      returned.  Defaults to 0.
    '''
    ordered = sorted(data)
    size = len(ordered)
    if size == 0:
        return default
    elif size % 2 == 1:
        return ordered[(size - 1) / 2]
    else:
        return (ordered[(size / 2)] + ordered[size / 2 - 1]) / 2.0


def meanstd(data):
    '''
    Returns the mean and standard deviation of the given data.

    Parameters:

    - ``data``: The data to find the mean and standard deviation of.
    '''
    try:
        mean = float(sum(data)) / len(data)
        std = math.sqrt(sum([(value - mean) ** 2 for value in data])
                        / len(data))
        return mean, std
    except (ZeroDivisionError, TypeError):
        return 0, 0


def binaryCounter(bits):
    '''
    Creates a generator that will count through all possible values for a set
    number of bits.  Returned in counting order.  For instance,
    ``binaryCounter(3)`` will yield, 000, 001, 010, 011 ... 110, 111.

    Parameters:

    - ``bits`` The number of bits in the binary counter.
    '''
    return itertools.product((0, 1), repeat=bits)
