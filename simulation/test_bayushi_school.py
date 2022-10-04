#!/usr/bin/env python3

#
# test_bayushi_school.py
#
# Unit tests for Bayushi Bushi School classes.
#

import logging
import sys
import unittest

from simulation import actions, bayushi_school
from simulation.character import Character
from simulation.log import logger
from simulation.roll_provider import TestRollProvider

# set up logging
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


class TestBayushiAttackStrategy(unittest.TestCase):
  def test_get_attack(self):
    bayushi = Character('Bayushi')
    target = Character('target')
    strategy = bayushi_school.BayushiAttackStrategy()
    action = strategy.get_attack_action(bayushi, target, 'attack')
    self.assertTrue(isinstance(action, actions.AttackAction))
    self.assertEqual(bayushi, action.subject())
    self.assertEqual(target, action.target())
    self.assertEqual('attack', action.skill()) 

  def test_get_feint(self):
    bayushi = Character('Bayushi')
    target = Character('target')
    strategy = bayushi_school.BayushiAttackStrategy()
    action = strategy.get_attack_action(bayushi, target, 'feint')
    self.assertTrue(isinstance(action, bayushi_school.BayushiFeintAction))
    self.assertEqual(bayushi, action.subject())
    self.assertEqual(target, action.target())
    self.assertEqual('feint', action.skill()) 


class TestBayushiWoundCheck(unittest.TestCase):
  def test_default_lw(self):
    bayushi = Character('Bayushi')
    bayushi.take_lw(50)
    roll = 30
    # Bayushi would take 3 SW from a normal Wound Check, but takes 0 from the school wound check
    self.assertEqual(0, bayushi_school.bayushi_wound_check(bayushi, roll))

  def test_large_damage(self):
    bayushi = Character('Bayushi')
    bayushi.take_lw(100)
    roll = 30
    # Bayushi would take 8 SW from a normal Wound Check, but takes 3 from the school wound check
    self.assertEqual(3, bayushi_school.bayushi_wound_check(bayushi, roll))

  def test_specified_lw(self):
    bayushi = Character('Bayushi')
    roll = 30
    # Bayushi would take 3 SW from a normal Wound Check, but takes 0 from the school wound check
    self.assertEqual(0, bayushi_school.bayushi_wound_check(bayushi, roll, lw=50))


class TestBayushiFeintAction(unittest.TestCase):
  def test_roll_damage(self):
    bayushi = Character('Bayushi')
    bayushi.set_skill('attack', 4)
    bayushi.set_skill('feint', 1)
    target = Character('target')
    # set Bayushi school roll parameter provider
    bayushi.set_roll_parameter_provider(bayushi_school.BayushiRollParameterProvider())
    # set test roll provider to rig damage roll
    roll_provider = TestRollProvider()
    roll_provider.put_damage_roll(9)
    bayushi.set_roll_provider(roll_provider)
    # set up Bayushi school Feint attack action
    action = bayushi_school.BayushiFeintAction(bayushi, target)
    action._attack_roll = 9001
    # assert expected behavior
    self.assertEqual(9, action.roll_damage())
    self.assertEqual((4, 1), roll_provider.pop_observed_params('damage'))

 
