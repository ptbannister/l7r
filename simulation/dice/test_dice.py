#!/usr/bin/env python3

#
# test_die.py
# Author: Patrick Bannister
# Unit tests for L7R dice simulators
#

import unittest

from dice.dice import Dice

class TestDice(unittest.TestCase):
  def test_ones(self):
    # roll five one-sided dice without exploding
    dice = Dice(5, 1, False)
    self.assertTrue(dice.roll() == [1, 1, 1, 1, 1])

if (__name__ == '__main__'):
  unittest.main()

