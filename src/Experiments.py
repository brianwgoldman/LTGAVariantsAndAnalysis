import os
import random
import HillClimber
from Individual import Individual
from LTGA import LTGA
import FitnessFunction
import Util


def createInitialPopulation(runNumber, evaluator, config):
    rngState = random.getstate()  # Stores the state of the RNG
    filename = os.pardir + os.sep + config["initialPopFolder"] + os.sep
    filename += "%(problem)s_%(dimensions)i_%(k)i_" % config
    filename += "%i.dat" % runNumber
    try:
        data = Util.loadConfiguration(filename)
    except IOError:
        data = []

    # Build new individuals if there aren't enough stored
    newInfo = len(data) < config["popSize"]
    while len(data) < config["popSize"]:
        row = {}
        genes = Util.randomBitString(config['dimensions'])
        evaluations = HillClimber.climb(genes, evaluator,
                                 HillClimber.steepestAscentHillClimber)
        iterations = evaluations / config['dimensions']
        fitness = evaluator.evaluate(genes)
        subproblems = evaluator.subProblemSolved(genes)
        try:
            # Keeps a running sum of current population
            total = data[-1]
            iterations += total['iterations']
            evaluations += total['evaluations']
            subproblems = [prev + curr for (prev, curr) in
                           zip(total['subproblems'], subproblems)]
        except IndexError:
            # No need to sum if no previous individuals
            pass
        minSubProblem = min(subproblems)
        row = {'iterations': iterations, 'evaluations': evaluations,
               'minSubProblem': minSubProblem, 'fitness': fitness,
               'genes': genes, 'subproblems': subproblems}
        data.append(row)
    if newInfo:
        Util.saveList(filename, data)
    # Trim extra information
    data = data[:config["popSize"]]
    population = [Individual(row["genes"], row["fitness"]) for row in data]
    # Get the last row's information about the population
    total = data[-1]
    random.setstate(rngState)  # Ensures RNG isn't modified by this function
    return  population, {"LS_iterations": total["iterations"],
                         "LS_evaluations": total["evaluations"],
                         "minSubProblem": total['minSubProblem']}


def oneRun(runNumber, optimizerClass, evaluator, config):
    population, result = createInitialPopulation(runNumber, evaluator, config)
    result["evaluations"] = 0

    bestFitness = max(population).fitness
    lookup = {individual.__hash__(): individual.fitness
              for individual in population}
    optimizer = optimizerClass().generate(population, config)
    individual = optimizer.next()  # Get the first individual
    while (result['evaluations'] < config["maximumEvaluations"] and
           bestFitness < config["maximumFitness"]):
        key = individual.__hash__()
        try:
            # If this individual has been rated before
            fitness = lookup[key]
        except KeyError:
            # Evaluate the individual
            fitness = evaluator.evaluate(individual.genes)
            if config['unique']:
                lookup[key] = fitness
            result['evaluations'] += 1
        if bestFitness < fitness:
            bestFitness = fitness
        try:
            # Send the fitness into the optimizer and get the next individual
            individual = optimizer.send(fitness)
        except StopIteration:
            break

    result['success'] = int(bestFitness >= config["maximumFitness"])
    if config['verbose']:
        print runNumber, result
    return result


def fullRun(config):
    try:
        random.seed(config["seed"])
    except KeyError:
        pass

    results = []
    for runNumber in range(config["runs"]):
        options = Util.moduleClasses(FitnessFunction)
        evaluator = options[config["problem"]](config)
        results.append(oneRun(runNumber, LTGA, evaluator, config))
    return results


def combineResults(results):
    combined = {}
    # Only gather results from successful runs
    successful = [result for result in results if result['success']]
    for result in successful:
        for key, value in result.iteritems():
            try:
                combined[key].append(value)
            except KeyError:
                combined[key] = [value]
    for key, value in combined.items():
        combined[key] = Util.meanstd(value)
    combined['success'] = len(successful) / float(len(results)), 0
    return combined
