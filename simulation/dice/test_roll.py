#!/usr/bin/env python3

#
# test_roll.py
# Author: Patrick Bannister
# Unit tests for L7R dice simulators
#

import unittest

from dice.mutator import ShosuroMutator
from dice.roll import Roll


class TestRoll(unittest.TestCase):
  def test_roll_ones(self):
    # roll 5k1 on one-sided dice without exploding
    roll = Roll(5, 1, faces=1, explode=False)
    # result should be 1 with no bonus
    self.assertTrue(roll.roll() == (1, 0))

  def test_roll_ones_shosuro(self):
    # roll 5k1 on one-sided dice without exploding
    # use the ShosuroMutator
    roll = Roll(5, 1, mutator_class=ShosuroMutator, faces=1, explode=False)
    # result should be 4 with a bonus of 3
    self.assertTrue(roll.roll() == (4, 3))


if (__name__ == '__main__'):
  unittest.main()

