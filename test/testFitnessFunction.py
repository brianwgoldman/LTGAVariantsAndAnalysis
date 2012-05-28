import unittest
import FitnessFunction


class TestTrapFunctions(unittest.TestCase):
    def setUp(self):
        self.config = {'k': 5, 'stepSize': 2}
        self.traps = 20

    def testDeceptiveTrap(self):
        box = FitnessFunction.DeceptiveTrap(self.config)
        self.assertEqual(box.evaluate([0, 0, 0, 0, 0] * self.traps), 4.0 / 5)
        self.assertEqual(box.evaluate([0, 1, 0, 0, 0] * self.traps), 3.0 / 5)
        self.assertEqual(box.evaluate([0, 0, 1, 1, 0] * self.traps), 2.0 / 5)
        self.assertEqual(box.evaluate([1, 1, 0, 0, 1] * self.traps), 1.0 / 5)
        self.assertEqual(box.evaluate([1, 1, 1, 1, 0] * self.traps), 0.0 / 5)
        self.assertEqual(box.evaluate([1, 1, 1, 1, 1] * self.traps), 5.0 / 5)

    def testDeceptiveStepTrap(self):
        box = FitnessFunction.DeceptiveStepTrap(self.config)
        self.assertEqual(box.evaluate([0, 0, 0, 0, 0] * self.traps), 2.0 / 3)
        self.assertEqual(box.evaluate([0, 1, 0, 0, 0] * self.traps), 2.0 / 3)
        self.assertEqual(box.evaluate([0, 0, 1, 1, 0] * self.traps), 1.0 / 3)
        self.assertEqual(box.evaluate([1, 1, 0, 0, 1] * self.traps), 1.0 / 3)
        self.assertEqual(box.evaluate([1, 1, 1, 1, 0] * self.traps), 0.0 / 3)
        self.assertEqual(box.evaluate([1, 1, 1, 1, 1] * self.traps), 3.0 / 3)
