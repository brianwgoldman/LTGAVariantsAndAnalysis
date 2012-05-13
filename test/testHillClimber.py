import unittest
from src import HillClimber, FitnessFunction


class TestHillClimber(unittest.TestCase):
    def setUp(self):
        self.oneMax = FitnessFunction.OneMax(None)
        self.dimensions = 10

    def testSteepestAscentHillClimber(self):
        genes = [0] * self.dimensions
        target = [1] * self.dimensions
        climber = HillClimber.steepestAscentHillClimber(genes)
        iteration = climber.next()
        while True:
            try:
                iteration = climber.send(self.oneMax.evaluate(iteration))
            except StopIteration:
                break
        self.assertEqual(genes, target)
