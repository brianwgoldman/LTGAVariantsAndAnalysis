import argparse
import Experiments
import Util

description = 'Linkage Tree Genetic Algorithms: Variants and Analysis code'
parser = argparse.ArgumentParser(description=description)
parser.add_argument('configs', metavar='Configuration Files',
                    type=str, nargs='+',
                    help='One or more json formatted files containing' +
                        ' configuration information')

parser.add_argument('-p', dest='popSize', type=int,
                    help='Use specified population size')

parser.add_argument('-b', dest='bisection', action='store_true',
                    help='Sets population size using bisection')

parser.add_argument('-c', dest='output_config', type=str,
                    help='Outputs single configuration file containing' +
                    ' the entire configuration used in this run')

parser.add_argument('-v', dest='verbose', action='store_true',
                    help='Include this flag to increase periodic output')

args = parser.parse_args()
config = Util.loadConfigurations(args.configs)
config['verbose'] = args.verbose

if args.popSize != None:
    config['popSize'] = args.popSize

if 'popSize' not in config or args.bisection:
    if args.verbose:
        print 'Using bisection to determine minimum population size'
    Experiments.bisection(config)

try:
    rawResults = Experiments.fullRun(config)
    combinedResults = Experiments.combineResults(rawResults)

    print combinedResults
except KeyError as e:
    print 'You must include a configuration value for', e.args[0]

if args.output_config != None:
    Util.saveConfiguration(args.output_config, config)
