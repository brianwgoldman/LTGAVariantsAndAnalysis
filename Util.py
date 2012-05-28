import inspect
import json
import random
import math
import os
import itertools


def classMethods(classType):
    return dict(inspect.getmembers(classType, inspect.ismethod))


def moduleClasses(module):
    return dict(inspect.getmembers(module, inspect.isclass))


def loadConfiguration(filename, fileMethod=open):
    with fileMethod(filename, 'r') as f:
        return json.load(f)


def loadConfigurations(filenames, fileMethod=open):
    result = {}
    for filename in filenames:
        result.update(loadConfiguration(filename, fileMethod))
    return result


def saveConfiguration(filename, data, fileMethod=open):
    with fileMethod(filename, 'w') as f:
        json.dump(data, f)


def saveList(filename, data):
    with open(filename, 'w') as f:
        f.write('[' + os.linesep)
        for lineNumber, line in enumerate(data):
            json.dump(line, f)
            if lineNumber != len(data) - 1:
                f.write(",")
            f.write(os.linesep)
        f.write(']' + os.linesep)


def randomBitString(length):
    generated = bin(random.getrandbits(length))[2:]  # String of bits
    leadingZeros = '0' * (length - len(generated)) + generated
    return map(int, leadingZeros)


def median(data, default=0):
    ordered = sorted(data)
    size = len(ordered)
    if size == 0:
        return default
    elif size % 2 == 1:
        return ordered[(size - 1) / 2]
    else:
        return (ordered[(size / 2)] + ordered[size / 2 - 1]) / 2.0


def meanstd(data):
    try:
        mean = float(sum(data)) / len(data)
        std = math.sqrt(sum([(value - mean) ** 2 for value in data])
                        / len(data))
        return mean, std
    except (ZeroDivisionError, TypeError):
        return 0, 0


def binaryCounter(bits):
    return itertools.product((0, 1), repeat=bits)
