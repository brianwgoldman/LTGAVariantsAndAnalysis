import math
import random
from itertools import combinations
import Util
import Individual


class LTGA(object):
    def getMaskValue(self, individual, mask):
        return tuple(individual.genes[g] for g in mask)

    def setMaskValues(self, individual, mask, value):
        for valueIndex, geneIndex in enumerate(mask):
            individual.genes[geneIndex] = value[valueIndex]

    def entropy(self, mask, lookup):
        try:
            return lookup[mask]
        except KeyError:
            occurances = {}
            for individual in self.individuals:
                # extract the gene values for the cluster
                value = self.getMaskValue(individual, mask)
                try:
                    occurances[value] += 1
                except KeyError:
                    occurances[value] = 1
            total = float(len(self.individuals))
            result = -sum(x / total * math.log(x / total, 2)
                          for x in occurances.itervalues())
            lookup[mask] = result
            return result

    def clusterDistance(self, c1, c2, lookup):
        try:
            return lookup[c1, c2]
        except KeyError:
            try:
                result = 2 - ((self.entropy(c1, lookup) +
                               self.entropy(c2, lookup))
                              / self.entropy(c1 + c2, lookup))
            except ZeroDivisionError:
                result = 2  # Zero divison only happens in 0/0
            lookup[c1, c2] = result
            lookup[c2, c1] = result
            return result

    def pairwiseDistance(self, c1, c2, lookup):
        try:
            return lookup[c1, c2]
        # averages the pairwise distance between each cluster
        except KeyError:
            result = sum(self.clusterDistance((a,), (b,), lookup)
                         for a in c1 for b in c2) / float(len(c1) * len(c2))
            lookup[c1, c2] = result
            lookup[c2, c1] = result
            return result

    def buildTree(self, distance):
        clusters = [(i,) for i in xrange(len(self.individuals[0].genes))]
        subtrees = [(i,) for i in xrange(len(self.individuals[0].genes))]
        random.shuffle(clusters)
        random.shuffle(subtrees)
        lookup = {}

        def allLowest():
            minVal = 3  # Max possible distance should be 2
            results = []
            for c1, c2 in combinations(clusters, 2):
                result = distance(c1, c2, lookup)
                if result < minVal:
                    minVal = result
                    results = [(c1, c2)]
                if result == minVal:
                    results.append((c1, c2))
            return results

        while len(clusters) > 1:
            c1, c2 = random.choice(allLowest())
            clusters.remove(c1)
            clusters.remove(c2)
            combined = c1 + c2
            clusters.append(combined)
            # Only add it as a subtree if it is not the root
            if len(clusters) != 1:
                subtrees.append(combined)
        return subtrees

    def leastLinkedFirst(self, subtrees):
        return list(reversed(subtrees))

    def smallestFirst(self, subtrees):
        return sorted(subtrees, key=len)

    def applyMask(self, p1, p2, mask):
        return Individual.Individual([p2.genes[g] if g in mask else p1.genes[g]
                                      for g in range(len(p1.genes))])

    def twoParentCrossover(self, masks):
        offspring = []
        # Does the following twice in order to make enough children
        for _ in [0, 1]:
            random.shuffle(self.individuals)
            for i in xrange(0, len(self.individuals) - 1, 2):
                p1 = self.individuals[i]
                p2 = self.individuals[i + 1]
                for mask in masks:
                    c1 = self.applyMask(p1, p2, mask)
                    c2 = self.applyMask(p2, p1, mask)
                    c1.fitness = yield c1
                    c2.fitness = yield c2
                    # if the best child is better than the best parent
                    if max(p1, p2) < max(c1, c2):
                        p1, p2 = c1, c2
                # Overwrite the parents with the modified version
                self.individuals[i] = p1
                self.individuals[i + 1] = p2
                # The offspring is the best individual created during the cross
                offspring.append(max(p1, p2))
        self.individuals = offspring

    def globalCrossover(self, masks):
        values = {mask: [] for mask in masks}
        for mask in masks:
            for individual in self.individuals:
                value = self.getMaskValue(individual, mask)
                values[mask].append(value)
        for individual in self.individuals:
            for mask in masks:
                startingValue = self.getMaskValue(individual, mask)
                options = [value for value in values[mask]
                           if value != startingValue]
                if len(options) > 0:
                    value = random.choice(options)
                    self.setMaskValues(individual, mask, value)
                    newFitness = yield individual
                    # if the individual improved, update fitness
                    if individual.fitness < newFitness:
                        individual.fitness = newFitness
                    # The individual did not improve, revert changes
                    else:
                        self.setMaskValues(individual, mask, startingValue)

    def generate(self, initialPopulation, config):
        self.individuals = initialPopulation
        distance = Util.classMethods(self)[config["distance"]]
        ordering = Util.classMethods(self)[config["ordering"]]
        crossover = Util.classMethods(self)[config["crossover"]]
        currentIndividuals = set(self.individuals)
        while True:
            previousIndividuals = currentIndividuals
            subtrees = self.buildTree(distance)
            masks = ordering(subtrees)
            generator = crossover(masks)
            individual = generator.next()
            while True:
                fitness = yield individual
                try:
                    individual = generator.send(fitness)
                except StopIteration:
                    break
            # If all individuals are identical
            currentIndividuals = set(self.individuals)
            if (len(currentIndividuals) == 1 or
                currentIndividuals == previousIndividuals):
                break
