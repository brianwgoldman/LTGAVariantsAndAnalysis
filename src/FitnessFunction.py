import random
import os
from operator import itemgetter
from Util import binaryCounter, loadConfiguration, saveConfiguration


class FitnessFunction(object):
    def __init__(self, config, runNumber):
        pass

    def evaluate(self, genes):
        raise Exception("Fitness function did not override evaluate")

    def subProblemSolved(self, genes):
        raise Exception("Fitness function did not override subProblemSolved")


class OneMax(FitnessFunction):
    def evaluate(self, genes):
        return sum(genes)

    def subProblemSolved(self, genes):
        return [int(sum(genes) == len(genes))]


class DeceptiveTrap(FitnessFunction):
    def __init__(self, config, _=None):
        self.trapSize = config["k"]

    def scoreTrap(self, genes):
        trap = sum(genes)
        return trap if trap == self.trapSize else self.trapSize - trap - 1

    def normalize(self, genes, fitness):
        return fitness / float(len(genes))

    def evaluate(self, genes):
        fitness = 0
        # iterate to find the start of each trap
        for i in xrange(0, len(genes), self.trapSize):
            # sum all of the values in that trap together
            fitness += self.scoreTrap(genes[i:i + self.trapSize])
        return self.normalize(genes, fitness)

    def subProblemSolved(self, genes):
        return [int(sum(genes[i:i + self.trapSize]) == self.trapSize)
                for i in xrange(0, len(genes), self.trapSize)]


class DeceptiveStepTrap(DeceptiveTrap):
    def __init__(self, config, _=None):
        DeceptiveTrap.__init__(self, config)
        self.stepSize = config["stepSize"]
        self.offset = (self.trapSize - self.stepSize) % self.stepSize
        self.possiblePerGene = ((self.trapSize / self.stepSize + self.offset)
                                / float(self.trapSize))

    def scoreTrap(self, genes):
        trap = DeceptiveTrap.scoreTrap(self, genes)
        return (self.offset + trap) / self.stepSize

    def normalize(self, genes, fitness):
        return fitness / (len(genes) * self.possiblePerGene)


class NearestNeighborNK(FitnessFunction):
    def __init__(self, config, runNumber):
        self.k = config['k']
        self.n = config['dimensions']
        problemNumber = config['problemSeed'] + runNumber
        self.buildProblem(config, problemNumber)

    def buildProblem(self, config, problemNumber):
        self.epistasis = [itemgetter(*[(g + i) % self.n
                                       for i in range(self.k + 1)])
                          for g in range(self.n)]
        key = "%(dimensions)i_%(k)i_" % config
        key += str(problemNumber)
        filename = config["nkProblemFolder"] + os.sep + key
        try:
            loaded = loadConfiguration(filename)
            self.min, self.max, self.optimal, self.fitness = loaded
        except IOError:
            rng = random.Random(problemNumber)
            self.fitness = [[rng.random() for _ in range(2 ** (self.k + 1))]
                            for _ in xrange(self.n)]
            self.min, _ = self.solve(min)
            self.max, self.optimal = self.solve(max)
            saveConfiguration(filename, (self.min, self.max,
                                         self.optimal, self.fitness))

    def evaluate(self, genes):
        fitness = 0
        for g, subProblem in enumerate(self.epistasis):
            fitness += self.getFitness(g, subProblem(genes))
        return round((fitness - self.min) / (self.max - self.min), 6)

    def getFitness(self, g, neighborhood):
        return self.fitness[g][int(''.join(map(str, neighborhood)), 2)]

    def subProblemSolved(self, genes):
        return [int(subProblem(genes) == subProblem(self.optimal))
                for subProblem in self.epistasis]

    def solve(self, extreme):
        known = {}

        def multiF(chunk, a, b):
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
        optimalString = a + c
        last = c
        for i in range(2, self.n / self.k):
            last = known[i, last, a]
            optimalString += last
        return fitness, map(int, optimalString)
