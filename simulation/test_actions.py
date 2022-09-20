#!/usr/bin/env python3

#
# test_actions.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator actions module
#

import unittest

from simulation.actions import AttackAction
from simulation.character import Character
from simulation.roll_provider import TestRollProvider


class TestAttackAction(unittest.TestCase):
  def test_calculate_extra_damage_dice(self):
    attacker = Character('attacker')
    target = Character('target')
    target.set_skill('parry', 5)
    # rig the attack roll to hit by 1
    # attack should get no extra damage dice
    attack = AttackAction(attacker, target)
    attack._attack_roll = 31
    self.assertEqual(0, attack.calculate_extra_damage_dice())
    # rig the attack roll to hit by 5
    # expect one extra damage die
    attack._attack_roll = 35
    self.assertEqual(1, attack.calculate_extra_damage_dice())
    # rig the attack roll to hit by 9
    # expect one extra damage die
    attack._attack_roll = 39
    self.assertEqual(1, attack.calculate_extra_damage_dice())
    # rig the attack roll to hit by 21
    # expect four extra damage dice
    attack._attack_roll = 51
    self.assertEqual(4, attack.calculate_extra_damage_dice())
    
  def test_calculate_extra_damage_dice_parried(self):
    attacker = Character('attacker')
    target = Character('target')
    target.set_skill('parry', 5)
    # set up an attack with a parry attempted
    attack = AttackAction(attacker, target)
    attack.set_parry_attempted()
    # rig the attack roll to hit by 1
    # attack should get no extra damage dice
    attack._attack_roll = 31
    self.assertEqual(0, attack.calculate_extra_damage_dice())
    # rig the attack roll to hit by 21
    # expect four extra damage dice
    attack._attack_roll = 51
    self.assertEqual(0, attack.calculate_extra_damage_dice())
  
  def test_hit(self):
    # attacker
    attacker = Character('attacker')
    # target
    target = Character('target')
    target.set_skill('parry', 5)
    # target's TN to hit should be 30
    # set attack roll to 31
    # attack should hit
    attack = AttackAction(attacker, target)
    attack._attack_roll = 31
    self.assertTrue(attack.is_hit())

  def test_hit_parried(self):
    # attacker
    attacker = Character('attacker')
    # target
    target = Character('target')
    target.set_skill('parry', 5)
    # target's TN to hit should be 30
    # set attack roll to 31 so it would have been good enough to hit
    attack = AttackAction(attacker, target)
    attack._attack_roll = 31
    self.assertTrue(attack.is_hit())
    # now set attack to be parried - it is no longer a hit
    attack.set_parried()
    self.assertFalse(attack.is_hit())

  def test_miss(self):
    # attacker
    attacker = Character('attacker')
    # target
    target = Character('target')
    target.set_skill('parry', 5)
    # target's TN to hit should be 30
    # set attack roll to 29
    # attack should miss
    attack = AttackAction(attacker, target)
    attack._attack_roll = 29
    self.assertFalse(attack.is_hit())


if (__name__ == '__main__'):
  unittest.main()

