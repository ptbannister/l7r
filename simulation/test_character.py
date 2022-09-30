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


class TestCharacter(unittest.TestCase):
  def test_base_to_hit_tn(self):
    akagi = Character('Akagi')
    shiba = Character('Shiba')
    shiba.set_skill('parry', 5)
    self.assertEqual(10, akagi.tn_to_hit())
    self.assertEqual(30, shiba.tn_to_hit())

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
    target = Character('target')
    self.assertEqual(1, akodo.roll_skill(target, 'attack'))
    self.assertEqual(3, akodo.roll_skill(target, 'parry'))
    self.assertEqual(4, akodo.roll_skill(target, 'double attack'))
    self.assertEqual(2, akodo.roll_skill(target, 'attack'))

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

  def test_vp(self):
    character = Character()
    # character with all 2s has 2 VP to spend
    self.assertEqual(2, character.max_vp())
    self.assertEqual(2, character.vp())
    # raise some rings but leave a ring at 2
    character.set_ring('air', 2)
    character.set_ring('earth', 3)
    character.set_ring('fire', 4)
    character.set_ring('water', 3)
    character.set_ring('void', 3)
    # character with high rings but one ring at 2 still has 2 VP to spend
    self.assertEqual(2, character.max_vp())
    self.assertEqual(2, character.vp())
    # raise lowest ring to 3
    character.set_ring('air', 3)
    # character should have 3 VP
    self.assertEqual(3, character.max_vp())
    self.assertEqual(3, character.vp())
    # give the character 3 worldliness
    character.set_skill('worldliness', 3)
    # character should have 6 VP
    self.assertEqual(6, character.max_vp())
    self.assertEqual(6, character.vp())
    # spend some vp
    character.spend_vp(2)
    # character's max should be unchanged, but available should be lower
    self.assertEqual(6, character.max_vp())
    self.assertEqual(4, character.vp())
    # spend down to zero
    character.spend_vp(4)
    self.assertEqual(6, character.max_vp())
    self.assertEqual(0, character.vp())
    # try to spend more, it should crash
    with self.assertRaises(ValueError):
      character.spend_vp(1)

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

