'''
This module contains coroutines designed to perform different types of hill
climbing as well as a function to perform a complete climb of a single set
of genes.
'''
import random


def steepestAscentHillClimber(genes):
    '''
    Given a initial list of binary genes, create a generator designed to yield
    each step in a steepest ascent hill climb.  Modifies the genes in place,
    such that when iteration ends the ``genes`` list contains the best found
    individual.

    Parameters:

    - ``genes``: The initial list of binary genes to improve using hill
      climbing.
    '''
    bestScore = yield genes
    while True:
        bestIndex = -1
        indicies = range(len(genes))
        # Breaks ties randomly
        random.shuffle(indicies)
        for index in indicies:
            # flip the bit at that index
            genes[index] = 1 - genes[index]
            score = yield genes
            if bestScore < score:
                bestScore = score
                bestIndex = index
            # flip the bit at that index back to its original value
            genes[index] = 1 - genes[index]
        if bestIndex != -1:
            genes[bestIndex] = 1 - genes[bestIndex]
        else:
            break


def climb(genes, evaluator, method):
    '''
    Improves the fitness of a list of binary genes using the given method on
    the specified evaluation function.  Modifies the genes in place and returns
    how many hill climbing evaluations were required to optimize the genes.

    Parameters:

    - ``genes``: The initial list of binary genes to improve using hill
      climbing.
    - ``evaluator``: A function that takes in a list of genes and returns its
      fitness.
    - ``method``: The hill climbing coroutine to be used.  For instance
      ``steepestAscentHillClimbing``.
    '''
    climber = method(genes)
    iteration = climber.next()
    counter = 0
    while True:
        counter += 1
        try:
            iteration = climber.send(evaluator.evaluate(iteration))
        except StopIteration:
            break
    return counter
