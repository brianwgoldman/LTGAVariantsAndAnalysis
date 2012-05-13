import sys
import math


class Individual(object):
    def __init__(self, genes=[], fitness=1 - sys.maxint):
        self.genes = genes
        self.fitness = fitness

    def distance(self, other):
        #TODO Consider removing
        return math.sqrt(sum([(mine - theirs) ** 2
                              for mine, theirs in
                              zip(self.genes, other.genes)]))

    def __cmp__(self, other):
        return other.fitness - self.fitness

    def __str__(self):
        return "(%s) = %s" % (",".join(map(str, self.genes)),
                              str(self.fitness))

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return int("".join(map(str, self.genes)), 2)
