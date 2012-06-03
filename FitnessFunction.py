'''
This module provides an interface for how fitness functions should interact
with solvers, as well as the definitions for a few benchmark problems
'''
import random
import os
from Util import binaryCounter, loadConfiguration, saveConfiguration


class FitnessFunction(object):
    '''
    An interface for a fitness function provided to ensure all required
    functions of a fitness function object are implemented
    '''
    def __init__(self, config, runNumber):
        '''
        Empty constructor, useful for fitness functions that are configuration
        and run independent
        '''
        pass

    def evaluate(self, genes):
        '''
        Empty function handle that throws an exception if not overridden.
        Given a list of genes, should return the fitness of those genes.
        '''
        raise Exception("Fitness function did not override evaluate")

    def subProblemsSolved(self, genes):
        '''
        Empty function handle that throws an exception if not overridden.
        Given a list of genes, returns a list of zeros and ones indicating
        which sub problems have been solved.  If this fitness function cannot
        be described as having subproblems, should return a list containing a
        single 1 or 0 indicating if these genes represent the global optimum.
        '''
        raise Exception("Fitness function did not override subProblemsSolved")


class DeceptiveTrap(FitnessFunction):
    '''
    Implementation of the deceptive trap benchmark.
    '''
    def __init__(self, config, _=None):
        '''
        Initializes the trap size used by this fitness function.  Ignores
        final argument as ``DeceptiveTrap``'s method of evaluation is run
        independent.

        Parameters:

        - ``config``: A configuration dictionary containing a value for ``k``
        to be used to set the trap size.
        '''
        self.trapSize = config["k"]

    def scoreTrap(self, genes):
        '''
        Given the set of genes in a trap, return the fitness of those genes.
        Automatically called by ``evaluate``.

        Parameters:

        - ``genes``: The list of genes to be scored.
        '''
        trap = sum(genes)
        return trap if trap == self.trapSize else self.trapSize - trap - 1

    def normalize(self, genes, fitness):
        '''
        Normalizes a fitness for a set of genes to be in the range [0-1], such
        that 1 is considered a successful run.  Automatically called by
        ``evaluate``.

        Parameters:

        - ``genes``: The list of genes being evaluated.
        - ``fitness``: The fitness value that needs to be normalized.
        '''
        return fitness / float(len(genes))

    def evaluate(self, genes):
        '''
        Given a list of binary genes, return the normalized fitness of those
        genes.

        Parameters:

        - ``genes``: The list of genes to be evaluated.
        '''
        fitness = 0
        # iterate to find the start of each trap
        for i in xrange(0, len(genes), self.trapSize):
            # sum all of the values in that trap together
            fitness += self.scoreTrap(genes[i:i + self.trapSize])
        return self.normalize(genes, fitness)

    def subProblemsSolved(self, genes):
        '''
        Returns a list of 0s and 1s indicating with of the traps contain the
        optimum value in the passed in genes.

        Parameters:

        - ``genes``: The list of genes to find solved subproblems in.
        '''
        return [int(sum(genes[i:i + self.trapSize]) == self.trapSize)
                for i in xrange(0, len(genes), self.trapSize)]


class DeceptiveStepTrap(DeceptiveTrap):
    '''
    Implementation of the deceptive step trap benchmark.  Inherits ``evaluate``
    and subProblemsSolved from ``DeceptiveTrap``.
    '''
    def __init__(self, config, _=None):
        '''
        Initializes the trap size and step size to be used in evaluation.
        Ignores final parameter as ``DeceptiveStepTrap`` method of evaluation
        is run number independent.

        Parameters:
        - ``config``: A configuration dictionary containing values for ``k``
          and ``stepSize`` to be used to set the trap size and step size used
          during evaluation.
        '''
        DeceptiveTrap.__init__(self, config)
        self.stepSize = config["stepSize"]
        self.offset = (self.trapSize - self.stepSize) % self.stepSize
        self.possiblePerGene = ((self.trapSize / self.stepSize + self.offset)
                                / float(self.trapSize))

    def scoreTrap(self, genes):
        '''
        Given a set of genes in a trap, returns the fitness of those genes.
        Calls ``DeceptiveTrap.scoreTrap`` to get the raw trap value, then
        modifies the fitness to include fitness plateaus.

        Parameters:

        - ``genes``: The genes for a single trap to be evaluated.
        '''
        trap = DeceptiveTrap.scoreTrap(self, genes)
        return (self.offset + trap) / self.stepSize

    def normalize(self, genes, fitness):
        '''
        Normalizes a fitness for a set of genes to be in the range [0-1], such
        that 1 is considered a successful run.  Automatically called by
        ``evaluate``.

        Parameters:

        - ``genes``: The list of genes being evaluated.
        - ``fitness``: The fitness value that needs to be normalized.
        '''
        return fitness / (len(genes) * self.possiblePerGene)


class NearestNeighborNK(FitnessFunction):
    '''
    An implementation of the nearest neighbor NK landscape benchmark.
    '''
    def __init__(self, config, runNumber):
        '''
        Initializes the fitness matrix and finds the global minimum and
        maximum for the given number of dimensions, overlap, and run number.
        If this configuration has been seen before, will load stored
        information from a file.

        Parameters:

        - ``config``: A dictionary containing all configuration information
          required to build an instance of the nearest neighbor NK problem.
          Should include values for:

          - ``k``: The amount of overlap for each sub problem.
          - ``dimensions``: The number of dimensions in this problem.
          - ``problemSeed``: The base seed for all runs, used when generating
            the fitness matrix.
          - ``nkProblemFolder``: The relative path to the folder where NK
            instances should be saved to and loaded from.
        '''
        self.k = config['k']
        self.n = config['dimensions']
        problemNumber = config['problemSeed'] + runNumber
        self.buildProblem(config, problemNumber)

    def buildProblem(self, config, problemNumber):
        '''
        Attempts to load the NK problem specified by the configuration and
        problem number.  If this problem has not been previously generated,
        this function will construct the fitness matrix and use ``solve`` to
        find the global minimum and maximum.

        Parameters:

        - ``config``: A dictionary containing all configuration information
          required to load/generate a NK problem.  Should include values
          for:

          - ``dimensions``: The number of dimensions in use
          - ``k``: The amount of gene overlap in the subproblems.
          - ``nkProblemFolder``: The relative path to the folder where NK
            instances should be saved to and loaded from.
        '''
        # Creates a list of neighborhoods, such that subproblem ``i`` depends
        # on self.epistasis[i]
        self.epistasis = [[(g + i) % self.n for i in range(self.k + 1)]
                          for g in range(self.n)]
        key = "%(dimensions)i_%(k)i_" % config
        key += str(problemNumber)
        filename = config["nkProblemFolder"] + os.sep + key
        try:
            loaded = loadConfiguration(filename)
            self.min, self.max, self.optimal, self.fitness = loaded
        except IOError:
            rng = random.Random(problemNumber)
            # Creates a random fitness matrix based on the problem number
            self.fitness = [[rng.random() for _ in range(2 ** (self.k + 1))]
                            for _ in xrange(self.n)]
            self.min, _ = self.solve(min)
            self.max, self.optimal = self.solve(max)
            saveConfiguration(filename, (self.min, self.max,
                                         self.optimal, self.fitness))

    def evaluate(self, genes):
        '''
        Given a list of binary genes, return the normalized fitness of those
        genes.

        Parameters:

        - ``genes``: The list of genes to be evaluated.
        '''
        fitness = 0
        for g, ep in enumerate(self.epistasis):
            # Convert the genes into a integer used to index the fitness matrix
            scalarized = int(''.join(map(str, [genes[x] for x in ep])), 2)
            fitness += self.fitness[g][scalarized]
        return round((fitness - self.min) / (self.max - self.min), 6)

    def getFitness(self, g, neighborhood):
        '''
        Given a gene index and the list of gene values in its neighborhood,
        return the fitness of the subproblem.

        Parameters:

        - ``g``: The subproblem to get the fitness for.
        - ``neighborhood``: The gene values contained in that subproblem
        '''
        return self.fitness[g][int(''.join(map(str, neighborhood)), 2)]

    def subProblemsSolved(self, genes):
        '''
        Returns a list of 0s and 1s indicating which subproblems currently
        have values identical to those for the global best genes.

        Parameters:

        - ``genes``: The genes to be checked for solved subproblems.
        '''
        return [int(all(genes[g] == self.optimal[g] for g in subProblem))
                for subProblem in self.epistasis]

    def solve(self, extreme):
        '''
        Returns the optimal value for this NK instance in polynomial time
        using dynamic programming.  For full explanation for how this
        algorithm works see:

        A. H. Wright, R. K. Thompson, and J. Zhang. The computational
        complexity of N-K fitness functions. IEEE Trans. on Evolutionary
        Computation, 4(4):373-379, 2000

        Parameters:

        - ``extreme``: A function that selects which fitness extreme is being
          solved for.  For instance, ``min`` or ``max``.
        '''
        # A dictionary mapping gene values for parts of the genome to their
        # fitness values
        known = {}

        def multiF(chunk, a, b):
            '''
            Internal function used to determine the fitness of a chunk of the
            genome.

            Parameters:

            - ``chuck``: Tuple of gene indices.
            - ``a``: First part of the gene settings for these indices.
            - ``b``: Second part of the gene settings for these indices.
            '''
            key = (chunk, a, b)
            try:
                return known[key]
            except:
                genewrap = (a + b) * 2
                known[key] = sum(self.getFitness(chunk * self.k + g,
                                                 genewrap[g:g + self.k + 1])
                                 for g in range(self.k))
                return known[key]

        for n in range(self.n / self.k - 1, 1, -1):
            v, u = {}, {}
            for a in binaryCounter(self.k):
                for c in binaryCounter(self.k):
                    u[a, c], v[a, c] = extreme((multiF(n - 1, a, b) +
                                                multiF(n, b, c), b)
                                               for b in binaryCounter(self.k))
            for a in binaryCounter(self.k):
                for c in binaryCounter(self.k):
                    known[n - 1, a, c] = u[a, c]
                    known[n, a, c] = v[a, c]

        fitness, a, c = extreme((multiF(0, a, c) +
                                 multiF(1, c, a), a, c)
                                for c in binaryCounter(self.k)
                                for a in binaryCounter(self.k))

        # Recreates the entire genome that receives the extreme fitness
        optimalString = a + c
        last = c
        for i in range(2, self.n / self.k):
            last = known[i, last, a]
            optimalString += last
        return fitness, map(int, optimalString)
