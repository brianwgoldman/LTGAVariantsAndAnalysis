'''
This module contains the code used to actually run experiments and to parse
the results of those experiments.
'''
import os
import random
import HillClimber
from Individual import Individual
from LTGA import LTGA
import FitnessFunction
import Util


def createInitialPopulation(runNumber, evaluator, config):
    '''
    Used to create the initial population for a given run on a specified
    problem.  Uses a ``HillClimber.steepestAscentHillClimber`` to optimize all
    individuals.  Will store results to the 'initialPopFolder' specified by
    ``config`` for future use, and will automatically load past saved
    information.  Returns the population and a dictionary describing features
    of that population as well as how it was created.

    Parameters:

    - ``runNumber``: What number run this population is for.  Ensures that
      populations created for this run in past experiments is reused and that
      all runs of a single experiment use different initial populations.
    - ``evaluator``: A ``FitnessFunction`` object used when optimizing the
      initial population
    - ``config``: A dictionary containing all configuration information
      required to generate initial individuals.  Should include values
      for:

      - ``initialPopFolder``: The relative path for where to save initial
        population information.
      - ``problem``: The name of the problem currently being solved.
      - ``dimensions``: The number of dimensions in the problem.
      - ``k``: The k value used by the problem.
      - ``popSize``: The population size to be created.
    '''
    rngState = random.getstate()  # Stores the state of the RNG
    filename = config["initialPopFolder"] + os.sep
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
        subproblems = evaluator.subProblemsSolved(genes)
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
    '''
    Performs a single run of LTGA in solving a specific problem.  Returns
    a dictionary of result information

    Parameters:

    - ``runNumber``: What number run this is
    - ``optimizerClass``: What class of optimizer to use, for instance ``LTGA``
    - ``evaluator``: The problem being solved, for instance
      ``FitnessFunction.DeceptiveTrap``, ``FitnessFunction.DeceptiveStepTrap``
      or ``FitnessFunction.NearestNeighborNK``.
    - ``config``: A dictionary containing all configuration information
      required to perform a single run.  Should include values for:

      - ``maximumEvaluations``: The hard limit on how many evaluations to
        perform.
      - ``maximumFitness``: The fitness required for a run to be considered a
        success.
      - ``unique``: A True / False value to determine if only unique evaluations
        should be counted
      - All configuration information required by ``createInitialPopulation``
        and any required by the ``optimizerClass``.
    '''
    population, result = createInitialPopulation(runNumber, evaluator, config)
    result["evaluations"] = 0

    bestFitness = max(population).fitness
    lookup = {int(individual): individual.fitness
              for individual in population}
    optimizer = optimizerClass().generate(population, config)
    individual = optimizer.next()  # Get the first individual
    while (result['evaluations'] < config["maximumEvaluations"] and
           bestFitness < config["maximumFitness"]):
        key = int(individual)
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
    '''
    Performs a full run of the specified configuration using ``oneRun``. Will
    return a list of result dictionaries describing what happened in each run.
    If a keyboard interrupt occurs, will return partial information.

    Parameters

    - ``config``: A dictionary containing all configuration information
      required to perform all runs.  Should include values for:

      - ``runs``: The number of runs to perform
      - ``problem``: The problem being solved, for instance ``DeceptiveTrap``,
        ``DeceptiveStepTrap`` or ``NearestNeighborNK``.
      - All configuration information required to initialize the
        ``FitnessFunction.``
      - All configuration information required by ``oneRun``.
    '''
    results = []
    try:
        for runNumber in range(config["runs"]):
            options = Util.moduleClasses(FitnessFunction)
            evaluator = options[config["problem"]](config, runNumber)
            results.append(oneRun(runNumber, LTGA, evaluator, config))
    except KeyboardInterrupt:
        print "Caught interrupt, exiting"
    return results


def combineResults(results):
    '''
    Given a list of result dictionaries, determine the mean and standard
    deviation for all key values.  Only combines results where the success
    key is true and the number of required evaluations is greater than zero
    (ensures the LTGA variant was actually used and successful).  Returns a
    dictionary containing all keys found in the original result objects, with
    the ``success`` key now set to the success rate

    Parameters:

    - ``results``: A list of dictionaries that recorded result information.
    '''
    combined = {}
    # Only gather results from successful runs and where local search
    # didn't solve the problem
    successful = [result for result in results
                  if result['success'] and result['evaluations'] != 0]
    for result in successful:
        for key, value in result.iteritems():
            try:
                combined[key].append(value)
            except KeyError:
                combined[key] = [value]
    for key, value in combined.items():
        combined[key] = Util.meanstd(value)
    runs = len([1 for result in results if result['evaluations'] != 0])
    try:
        combined['success'] = len(successful) / float(runs), 0
    except ZeroDivisionError:
        combined['success'] = 0, 0
    return combined


def bisection(config):
    '''
    Determines the minimum population size for a configuration that acceptably
    solves the specified problem using bisection.  Starts with a minimum
    population size of 2, this will double the population size until the
    success criteria are met.  It will then perform a binary search of the
    space between the lowest found successful population size and the highest
    found unsuccessful population size.  Modifies the input configuration
    dictionary to contain the minimum successful population size found.

    Parameters:

    - ``config``: A dictionary containing all configuration information
      required to perform bisection.  Should include values for:

      - ``bisectionRuns``: The number of runs to use a given population size in
        order to determine if it is successful.
      - ``problem``: The problem being solved, for instance ``DeceptiveTrap``,
        ``DeceptiveStepTrap`` or ``NearestNeighborNK``.
      - ``bisectionFailureLimit``: The maximum number of times a population
        size can fail to find the global optimum of a problem before it is
        marked as unsuccessful.  IE: A failure limit of 1 means it can fail one
        of the ``bisectionRuns`` without being marked as unsuccessful.
      - All configuration information required to initialize the
        ``FitnessFunction.``
      - All configuration information required by ``oneRun``.
    '''
    def canSucceed(config):
        failures = 0
        for runNumber in xrange(config["bisectionRuns"]):
            options = Util.moduleClasses(FitnessFunction)
            evaluator = options[config["problem"]](config, runNumber)
            result = oneRun(runNumber, LTGA, evaluator, config)
            if not result['success']:
                failures += 1
                if failures > config['bisectionFailureLimit']:
                    return False
        return True

    least, most = 0, 1
    while True:
        least = most
        most *= 2
        config['popSize'] = most
        if config['verbose']:
            print 'Trying population size', config['popSize']
        if canSucceed(config):
            break
    while least + 1 < most:
        config['popSize'] = (most + least) / 2
        if config['verbose']:
            print 'Trying population size', config['popSize']
        if canSucceed(config):
            most = config['popSize']
        else:
            least = config['popSize']
    config['popSize'] = most
    if config['verbose']:
        print 'Bisection set population size as', config['popSize']
