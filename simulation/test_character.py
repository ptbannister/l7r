#!/usr/bin/env python3

#
# test_character.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator Character classes
#

import unittest

from simulation.actions import AttackAction
from simulation.character import Character
from simulation.context import EngineContext
from simulation.events import AttackDeclaredEvent, NewPhaseEvent
from simulation.roll_provider import TestRollProvider
from simulation.strategy import AttackStrategy


class TestCharacter(unittest.TestCase):
  def test_base_to_hit_tn(self):
    akagi = Character('Akagi')
    shiba = Character('Shiba')
    shiba.set_skill('parry', 5)
    self.assertEqual(10, akagi.base_to_hit_tn())
    self.assertEqual(30, shiba.base_to_hit_tn())

  def test_roll_skill(self):
    roll_provider = TestRollProvider()
    roll_provider.put_skill_roll('attack', 1)
    roll_provider.put_skill_roll('attack', 2)
    roll_provider.put_skill_roll('parry', 3)
    roll_provider.put_skill_roll('double attack', 4)
    akodo = Character('Akodo')
    akodo.set_skill('attack', 5)
    akodo.set_skill('parry', 5)
    akodo.set_skill('double attack', 5)
    akodo.set_roll_provider(roll_provider)
    self.assertEqual(1, akodo.roll_skill('fire', 'attack'))
    self.assertEqual(3, akodo.roll_skill('air', 'parry'))
    self.assertEqual(4, akodo.roll_skill('fire', 'double attack'))
    self.assertEqual(2, akodo.roll_skill('fire', 'attack'))

  def test_speculative_wound_check(self):
    '''
    A "speculative" wound check is one where the LW are specified, instead of defaulting to the character's current LW total.
    '''
    akodo = Character('Akodo')
    # wound check exceeds LW: 0 SW
    self.assertEqual(0, akodo.wound_check(10, 9))
    # wound check misses by less than 10: 1 SW
    self.assertEqual(1, akodo.wound_check(5, 10))
    # wound check misses by 10: 2 SW
    self.assertEqual(2, akodo.wound_check(10, 20))
    # wound check misses by 19: 2 SW
    self.assertEqual(2, akodo.wound_check(10, 29))
    # wound check misses by 20: 3 SW
    self.assertEqual(3, akodo.wound_check(10, 30))

  def test_wound_check(self):
    akodo = Character('Akodo')
    akodo.take_lw(30)
    # wound check exceeds LW: 0 SW
    self.assertEqual(0, akodo.wound_check(31))
    # wound check misses by less than 10: 1 SW
    self.assertEqual(1, akodo.wound_check(25))
    # wound check misses by 10: 2 SW
    self.assertEqual(2, akodo.wound_check(20))
    # wound check misses by 19: 2 SW
    self.assertEqual(2, akodo.wound_check(19))
    # wound check misses by 20: 3 SW
    self.assertEqual(3, akodo.wound_check(10))


if (__name__ == '__main__'):
  unittest.main()

