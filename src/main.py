import argparse
import Experiments
import Util

description = 'Linkage Tree Genetic Algorithms: Variants and Analysis code'
parser = argparse.ArgumentParser(description=description)
parser.add_argument('configs', metavar='Configuration Files',
                    type=str, nargs='+',
                    help='One or more json formatted files containing' +
                        'configuration information')

parser.add_argument('-p', dest='popSize', type=int,
                    help='Use specified population size')

parser.add_argument('-v', dest='verbose', action='store_true',
                    help='Include this flag to increase periodic output')

args = parser.parse_args()

config = Util.loadConfigurations(args.configs)
if args.popSize != None:
    config['popSize'] = args.popSize
config['verbose'] = args.verbose

try:
    rawResults = Experiments.fullRun(config)
    combinedResults = Experiments.combineResults(rawResults)

    print combinedResults
except KeyError as e:
    print 'You must include a configuration value for', e.args[0]
