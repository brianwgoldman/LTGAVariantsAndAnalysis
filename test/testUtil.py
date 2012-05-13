import unittest
import random
from src import Util


class TestHillClimber(unittest.TestCase):
    def setUp(self):
        self.size = 100
        self.loops = 100
        self.even = range(self.size)
        self.odd = range(self.size + 1)

    def testMedianOdd(self):
        random.shuffle(self.odd)
        self.assertEqual(Util.median(self.odd), self.size / 2)

    def testMedianEven(self):
        random.shuffle(self.even)
        self.assertEqual(Util.median(self.even), self.size / 2 - 0.5)

    def testRandomBitString(self):
        for length in xrange(1, self.loops + 1):
            generated = Util.randomBitString(length)
            self.assertEqual(len(generated), length)
            self.assert_(all([element in [0, 1] for element in generated]))
