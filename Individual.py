'''
Simple module containing individual object implementations.
'''
import sys


class Individual(object):
    '''
    A basic individual object used to combine gene fitness with genomes, as
    well as some basic utility functions.
    '''
    def __init__(self, genes=[], fitness=1 - sys.maxint):
        '''
        Create a new individual instance with optional arguments for initial
        genes and fitness.

        Parameters:

        - ``genes``: The list of genes for the individual.  Defaults to empty.
        - ``fitness``: The fitness for the individual.  Defaults to very
          negative.
        '''
        self.genes = genes
        self.fitness = fitness

    def __cmp__(self, other):
        '''
        Compares to individuals based on their fitness.  Two individuals with
        that compare equal do not necessarily have the same genes, just the
        same fitness.

        Parameters:

        - ``other``: The other individual to compare with.
        '''
        if self.fitness > other.fitness:
            return 1
        elif self.fitness < other.fitness:
            return -1
        else:
            return 0

    def __str__(self):
        '''
        Converts the individual into a string representation useful for
        displaying an individual.
        '''
        return "(%s) = %s" % (",".join(map(str, self.genes)),
                              str(self.fitness))

    def __int__(self):
        '''
        Converts a binary individual's genes into a single integer.  Useful
        for uniqueness checking.
        '''
        return int("".join(map(str, self.genes)), 2)

    def __hash__(self):
        '''
        Returns the value of ``__int__``, used when determinging sets of unique
        individuals.
        '''
        return int(self)
