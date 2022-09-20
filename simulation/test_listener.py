#!/usr/bin/env python3

#
# test_listener.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator Listener classes
#

import logging
import sys
import unittest

from simulation.actions import AttackAction
from simulation.character import Character
from simulation.context import EngineContext
from simulation.events import DeathEvent, NewRoundEvent, LightWoundsDamageEvent, SeriousWoundsDamageEvent, TakeSeriousWoundEvent, UnconsciousEvent, WoundCheckDeclaredEvent, WoundCheckFailedEvent, WoundCheckRolledEvent, WoundCheckSucceededEvent
from simulation.listener import NewRoundListener, LightWoundsDamageListener, SeriousWoundsDamageListener, TakeSeriousWoundListener, WoundCheckDeclaredListener, WoundCheckFailedListener, WoundCheckRolledListener
from simulation.log import logger
from simulation.roll_provider import TestRollProvider


# set up logging
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


class TestNewRoundListener(unittest.TestCase):
  def test_new_round(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    # rig an initiative roll
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1, 2])
    character.set_roll_provider(roll_provider)
    event = NewRoundEvent(1)
    listener = NewRoundListener()
    result = listener.handle(character, event, context)
    self.assertTrue(result is None)
    self.assertEqual([1, 2], character.actions())


class TestLightWoundsDamageListener(unittest.TestCase):
  def test_light_wounds(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    context.load_probability_data()
    damage = 20
    event = LightWoundsDamageEvent(character, damage)
    listener = LightWoundsDamageListener()
    result = listener.handle(character, event, context)
    self.assertTrue(isinstance(result, WoundCheckDeclaredEvent))
    self.assertEqual(damage, result.damage)
    self.assertEqual(damage, character.lw())

  def test_additive_light_wounds(self):
    character = Character()
    character.take_lw(5)
    context = EngineContext([[character,], [Character(),]])
    context.load_probability_data()
    damage = 20
    event = LightWoundsDamageEvent(character, damage)
    listener = LightWoundsDamageListener()
    result = listener.handle(character, event, context)
    self.assertTrue(isinstance(result, WoundCheckDeclaredEvent))
    self.assertEqual(damage, result.damage)
    # character should now have 25 LW
    self.assertEqual(25, character.lw())


class TestSeriousWoundsDamageListener(unittest.TestCase):
  def test_die(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    damage = 5
    event = SeriousWoundsDamageEvent(character, damage)
    listener = SeriousWoundsDamageListener()
    result = listener.handle(character, event, context)
    self.assertTrue(isinstance(result, DeathEvent))
    self.assertEqual(character, result.subject)

  def test_unconscious(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    damage = 4
    event = SeriousWoundsDamageEvent(character, damage)
    listener = SeriousWoundsDamageListener()
    result = listener.handle(character, event, context)
    self.assertTrue(isinstance(result, UnconsciousEvent))
    self.assertEqual(character, result.subject)

  def test_wounds(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    damage = 2
    event = SeriousWoundsDamageEvent(character, damage)
    listener = SeriousWoundsDamageListener()
    result = listener.handle(character, event, context)
    self.assertTrue(result is None)
    self.assertEqual(2, character.sw())


class TestTakeSeriousWoundListener(unittest.TestCase):
  def test_take_sw(self):
    character = Character()
    character.take_lw(9001)
    context = EngineContext([[character,], [Character(),]])
    event = TakeSeriousWoundEvent(character, 1)
    listener = TakeSeriousWoundListener()
    result = listener.handle(character, event, context)
    self.assertTrue(isinstance(result, SeriousWoundsDamageEvent))
    self.assertEqual(result.damage, 1)
    # the character's lw should be reset, but the sw is not taken until the serious wound event is handled
    self.assertEqual(0, character.lw())
    self.assertEqual(0, character.sw())


class TestWoundCheckDeclaredListener(unittest.TestCase):
  def test_roll(self):
    # set up character with rigged wound check
    character = Character()
    roll_provider = TestRollProvider()
    roll_provider.put_wound_check_roll(50)
    character.set_roll_provider(roll_provider)
    context = EngineContext([[character,], [Character(),]])
    damage = 20
    vp = 0
    event = WoundCheckDeclaredEvent(character, damage, vp)
    listener = WoundCheckDeclaredListener()
    result = listener.handle(character, event, context)
    self.assertTrue(isinstance(result, WoundCheckRolledEvent))
    self.assertEqual(20, result.damage)
    self.assertEqual(50, result.roll)


class TestWoundCheckRolledListener(unittest.TestCase):
  def test_fail(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    damage = 20
    roll = 10
    event = WoundCheckRolledEvent(character, damage, roll)
    listener = WoundCheckRolledListener()
    result = listener.handle(character, event, context)
    self.assertTrue(isinstance(result, WoundCheckFailedEvent))
    self.assertEqual(damage, result.damage)
    self.assertEqual(roll, result.roll)

  def test_succeed(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    damage = 10
    roll = 20
    event = WoundCheckRolledEvent(character, damage, roll)
    listener = WoundCheckRolledListener()
    result = listener.handle(character, event, context)
    self.assertTrue(isinstance(result, WoundCheckSucceededEvent))
    self.assertEqual(damage, result.damage)
    self.assertEqual(roll, result.roll)


class TestWoundCheckFailedListener(unittest.TestCase):
  def test_fail(self):
    character = Character()
    character.take_lw(29)
    context = EngineContext([[character,], [Character(),]])
    damage = 20
    roll = 10
    event = WoundCheckFailedEvent(character, damage, roll)
    listener = WoundCheckFailedListener()
    result = listener.handle(character, event, context)
    # missing a wound check by 19 means 2 SW
    self.assertTrue(isinstance(result, SeriousWoundsDamageEvent))
    self.assertEqual(2, result.damage)
    # character's lw should be reset
    self.assertEqual(0, character.lw())


# TODO: test wound check succeeded listener


if (__name__ == '__main__'):
  unittest.main()

