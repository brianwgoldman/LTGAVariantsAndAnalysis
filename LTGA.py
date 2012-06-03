'''
This module contains the implementation of LTGA itself.  It includes
functionality for each of the variants
'''
import math
import random
from itertools import combinations
import Util
from Individual import Individual


class LTGA(object):
    '''
    Class containing all of the LTGA functionality.  Uses the coroutine
    design structure to interact with problems being optimized.  To use,
    create an LTGA object and then call the ``generate`` function.  This
    will send out individuals and expects their fitness to be sent back in.
    '''
    def getMaskValue(self, individual, mask):
        '''
        Gets the individual's gene values for the given mask

        Parameters:

        - ``individual``: The individual to get gene information from
        - ``mask``: The list of indices to get information from
        '''
        return tuple(individual.genes[g] for g in mask)

    def setMaskValues(self, individual, mask, value):
        '''
        Sets the individual's gene values for the given mask

        Parameters:

        - ``individual``: The individual who's genes are changing.
        - ``mask``: The list of indices to change.
        - ``value``: The list of values to change to.
        '''
        for valueIndex, geneIndex in enumerate(mask):
            individual.genes[geneIndex] = value[valueIndex]

    def entropy(self, mask, lookup):
        '''
        Calculates the current populations entropy for a given mask.

        Parameters:

        - ``mask``: The list of indices to examine
        - ``lookup``: A dictionary containing entropy values already found for
          this population.  Should be reset if the population changes.
        '''
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
        '''
        Calculates the true entropic distance between two clusters of genes.

        Parameters:

        - ``c1``: The first cluster.
        - ``c2``: The second cluster.
        - ``lookup``: A dictionary mapping cluster pairs to their previously
          found distances.  Should be reset if the population changes.
        '''
        try:
            return lookup[c1, c2]
        except KeyError:
            try:
                result = 2 - ((self.entropy(c1, lookup) +
                               self.entropy(c2, lookup))
                              / self.entropy(c1 + c2, lookup))
            except ZeroDivisionError:
                result = 2  # Zero division only happens in 0/0
            lookup[c1, c2] = result
            lookup[c2, c1] = result
            return result

    def pairwiseDistance(self, c1, c2, lookup):
        '''
        Calculates the pairwise approximation of the entropic distance between
        two clusters of genes.

        Parameters:

        - ``c1``: The first cluster.
        - ``c2``: The second cluster.
        - ``lookup``: A dictionary mapping cluster pairs to their previously
          found distances.  Should be reset if the population changes.
        '''
        try:
            return lookup[c1, c2]
        except KeyError:
            # averages the pairwise distance between each cluster
            result = sum(self.clusterDistance((a,), (b,), lookup)
                         for a in c1 for b in c2) / float(len(c1) * len(c2))
            lookup[c1, c2] = result
            lookup[c2, c1] = result
            return result

    def buildTree(self, distance):
        '''
        Given a method of calculating distance, build the linkage tree for the
        current population.  The tree is built by finding the two clusters with
        the minimum distance and merging them into a single cluster.  The
        process is initialized with all possible clusters of size 1 and ends
        when only a single cluster remains.  Returns the subtrees in the order
        they were created.

        Parameters:

        - ``distance``: The method of calculating distance.  Current options
          are ``self.clusterDistance`` and ``self.pairwiseDistance``
        '''
        clusters = [(i,) for i in xrange(len(self.individuals[0].genes))]
        subtrees = [(i,) for i in xrange(len(self.individuals[0].genes))]
        random.shuffle(clusters)
        random.shuffle(subtrees)
        lookup = {}

        def allLowest():
            '''
            Internal function used to find the list of all clusters pairings
            with the current smallest distances.
            '''
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
        '''
        Reorders the subtrees such that the cluster pairs with the least
        linkage appear first in the list.  Assumes incoming subtrees are
        ordered by when they were created by the ``self.buildTree`` function.

        Parameters:

        - ``subtrees``: The list of subtrees ordered by how they were
          originally created.
        '''
        return list(reversed(subtrees))

    def smallestFirst(self, subtrees):
        '''
        Reorders the subtrees such that the cluster pairs with the smallest
        number of genes appear first in the list.  Assumes incoming subtrees
        are ordered by when they were created by the ``self.buildTree``
        function.

        Parameters:

        - ``subtrees``: The list of subtrees ordered by how they were
          originally created.
        '''
        return sorted(subtrees, key=len)

    def applyMask(self, p1, p2, mask):
        '''
        Used by two parent crossover to create an individual by coping the
        genetic information from p2 into a clone of p1 for all genes in the
        given mask.  Returns the newly created individual.

        Parameters:

        - ``p1``: The first parent.
        - ``p2``: The second parent.
        - ``mask``: The list of indices used in this crossover.
        '''
        maskSet = set(mask)
        return Individual([p2.genes[g] if g in maskSet else p1.genes[g]
                           for g in range(len(p1.genes))])

    def twoParentCrossover(self, masks):
        '''
        Creates individual generator using the two parent crossover variant.
        Uses coroutines to send out individuals and receive their fitness
        values.  Terminates when a complete evolutionary generation has
        finished.

        Parameters:

        - ``masks``: The list of crossover masks to be used when generating
          individuals, ordered based on how they should be applied.
        '''
        offspring = []
        # Does the following twice in order to make enough children
        for _ in [0, 1]:
            random.shuffle(self.individuals)
            # pairs off parents with their neighbor
            for i in xrange(0, len(self.individuals) - 1, 2):
                p1 = self.individuals[i]
                p2 = self.individuals[i + 1]
                for mask in masks:
                    c1 = self.applyMask(p1, p2, mask)
                    c2 = self.applyMask(p2, p1, mask)
                    # Duplicates are caught higher up
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
        '''
        Creates individual generator using the global crossover variant.
        Uses coroutines to send out individuals and receive their fitness
        values.  Terminates when a complete evolutionary generation has
        finished.

        Parameters:

        - ``masks``: The list of crossover masks to be used when generating
          individuals, ordered based on how they should be applied.
        '''
        # Creates a dictionary to track individual's values for each mask
        values = {mask: [] for mask in masks}
        for mask in masks:
            for individual in self.individuals:
                value = self.getMaskValue(individual, mask)
                values[mask].append(value)
        # each individual creates a single offspring, which replaces itself
        for individual in self.individuals:
            for mask in masks:
                startingValue = self.getMaskValue(individual, mask)
                # Find the list of values in the population that differ from
                # the current individual's values for this mask
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
        '''
        The individual generator for the LTGA population.  Sends out
        individuals that need to be evaluated and receives fitness information.
        Will continue sending out individuals until the population contains
        only one unique individual or a generation passes without the set of
        unique individuals changing.

        Parameters:

        - ``initialPopulation``: The list of individuals to be used as the
          basis for LTGA's evolution.  These individuals should already have
          fitness values set.  If local search is to be performed on the
          initial population, it should be done before sending to this
          function.
        - ``config``: A dictionary containing all configuration information
          required by LTGA to generate individuals.  Should include values
          for:

          - ``distance``: The method used to determine the distance between
            clusters, for instance ``clusterDistance`` and
            ``pairwiseDistance``.
          - ``ordering``: The method used to determine what order subtrees
            should be used as crossover masks, for instance
            ``leastLinkedFirst`` and ``smallestFirst``.
          - ``crossover``: The method used to generate new individuals, for
            instance ``twoParentCrossover`` and ``globalCrossover``.
        '''
        self.individuals = initialPopulation
        distance = Util.classMethods(self)[config["distance"]]
        ordering = Util.classMethods(self)[config["ordering"]]
        crossover = Util.classMethods(self)[config["crossover"]]
        beforeGenerationSet = set(self.individuals)
        while True:
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
            currentSet = set(self.individuals)
            if (len(currentSet) == 1 or
                currentSet == beforeGenerationSet):
                break
            beforeGenerationSet = currentSet
