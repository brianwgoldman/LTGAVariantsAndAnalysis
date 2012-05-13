import inspect
import json
import random


def classMethods(classType):
    return dict(inspect.getmembers(classType, inspect.ismethod))


def loadConfiguration(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def loadConfigurations(filenames):
    result = {}
    for filename in filenames:
        result.update(loadConfiguration(filename))
    return result


def saveConfiguration(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)


def randomBitString(length):
    generated = bin(random.getrandbits(length))[2:]  # String of bits
    leadingZeros = '0' * (length - len(generated)) + generated
    return map(int, leadingZeros)
