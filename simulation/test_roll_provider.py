#!/usr/bin/env python3

#
# test_roll_provider.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator roll_provider module
#

import unittest

from simulation.roll_provider import TestRollProvider


class TestTestRollProvider(unittest.TestCase):
  def test_fifo(self):
    roll_provider = TestRollProvider()
    roll_provider.put_skill_roll('attack', 37)
    roll_provider.put_skill_roll('attack', 9001)
    # first Attack roll should be 37
    self.assertEqual(37, roll_provider.get_skill_roll('fire', 'attack'))
    # second Attack roll should be 9001
    self.assertEqual(9001, roll_provider.get_skill_roll('fire', 'attack'))

  def test_get_initiative_roll(self):
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1, 2, 3]) 
    roll_provider.put_initiative_roll([1, 5, 10])
    self.assertEqual([1, 2, 3], roll_provider.get_initiative_roll())
    self.assertEqual([1, 5, 10], roll_provider.get_initiative_roll())

  def test_get_skill_roll(self):
    roll_provider = TestRollProvider()
    roll_provider.put_skill_roll('attack', 37)
    roll_provider.put_skill_roll('parry', 59009)
    # should get different results for Attack and Parry
    self.assertEqual(37, roll_provider.get_skill_roll('fire', 'attack'))
    self.assertEqual(59009, roll_provider.get_skill_roll('air', 'parry'))

  def test_get_wound_check_roll(self):
    roll_provider = TestRollProvider()
    roll_provider.put_wound_check_roll(5)
    roll_provider.put_wound_check_roll(50)
    self.assertEqual(5, roll_provider.get_wound_check_roll())
    self.assertEqual(50, roll_provider.get_wound_check_roll())

  def test_no_roll_queued(self):
    roll_provider = TestRollProvider()
    with self.assertRaises(KeyError):
      roll_provider.get_skill_roll('fire', 'attack')

if (__name__ == '__main__'):
  unittest.main()

