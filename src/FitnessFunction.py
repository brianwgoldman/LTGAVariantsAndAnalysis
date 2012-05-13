class FitnessFunction(object):
    def evaluate(self, genes):
        raise Exception("Fitness function did not override eval")


class DeceptiveTrap(FitnessFunction):
    def __init__(self, config):
        self.trapSize = config["trapSize"]

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


class DeceptiveStepTrap(DeceptiveTrap):
    def __init__(self, config):
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
