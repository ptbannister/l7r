#!/usr/bin/env python3

#
# test_listeners.py
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
from simulation.listeners import NewRoundListener, LightWoundsDamageListener, SeriousWoundsDamageListener, TakeSeriousWoundListener, WoundCheckDeclaredListener, WoundCheckFailedListener, WoundCheckRolledListener
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
    responses = list(listener.handle(character, event, context))
    self.assertTrue(responses == [])
    self.assertEqual([1, 2], character.actions())


class TestLightWoundsDamageListener(unittest.TestCase):
  def test_light_wounds(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    context.load_probability_data()
    damage = 20
    event = LightWoundsDamageEvent(character, damage)
    listener = LightWoundsDamageListener()
    responses = list(listener.handle(character, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, WoundCheckDeclaredEvent))
    self.assertEqual(damage, response.damage)
    self.assertEqual(damage, character.lw())

  def test_additive_light_wounds(self):
    character = Character()
    character.take_lw(5)
    context = EngineContext([[character,], [Character(),]])
    context.load_probability_data()
    damage = 20
    event = LightWoundsDamageEvent(character, damage)
    listener = LightWoundsDamageListener()
    responses = list(listener.handle(character, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, WoundCheckDeclaredEvent))
    self.assertEqual(damage, response.damage)
    # character should now have 25 LW
    self.assertEqual(25, character.lw())


class TestSeriousWoundsDamageListener(unittest.TestCase):
  def test_die(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    damage = 5
    event = SeriousWoundsDamageEvent(character, damage)
    listener = SeriousWoundsDamageListener()
    responses = list(listener.handle(character, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, DeathEvent))
    self.assertEqual(character, response.subject)

  def test_unconscious(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    damage = 4
    event = SeriousWoundsDamageEvent(character, damage)
    listener = SeriousWoundsDamageListener()
    responses = list(listener.handle(character, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, UnconsciousEvent))
    self.assertEqual(character, response.subject)

  def test_wounds(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    damage = 2
    event = SeriousWoundsDamageEvent(character, damage)
    listener = SeriousWoundsDamageListener()
    responses = list(listener.handle(character, event, context))
    self.assertEqual([], responses)
    self.assertEqual(damage, character.sw())


class TestTakeSeriousWoundListener(unittest.TestCase):
  def test_take_sw(self):
    character = Character()
    character.take_lw(9001)
    context = EngineContext([[character,], [Character(),]])
    event = TakeSeriousWoundEvent(character, 1)
    listener = TakeSeriousWoundListener()
    responses = list(listener.handle(character, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, SeriousWoundsDamageEvent))
    self.assertEqual(character, response.target)
    self.assertEqual(1, response.damage) 
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
    responses = list(listener.handle(character, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, WoundCheckRolledEvent))
    self.assertEqual(20, response.damage)
    self.assertEqual(50, response.roll)


class TestWoundCheckRolledListener(unittest.TestCase):
  def test_fail(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    damage = 20
    roll = 10
    event = WoundCheckRolledEvent(character, damage, roll)
    listener = WoundCheckRolledListener()
    responses = list(listener.handle(character, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, WoundCheckFailedEvent))
    self.assertEqual(damage, response.damage)
    self.assertEqual(roll, response.roll)

  def test_succeed(self):
    character = Character()
    context = EngineContext([[character,], [Character(),]])
    damage = 10
    roll = 20
    event = WoundCheckRolledEvent(character, damage, roll)
    listener = WoundCheckRolledListener()
    responses = list(listener.handle(character, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, WoundCheckSucceededEvent))
    self.assertEqual(damage, response.damage)
    self.assertEqual(roll, response.roll)


class TestWoundCheckFailedListener(unittest.TestCase):
  def test_fail(self):
    character = Character()
    character.take_lw(29)
    context = EngineContext([[character,], [Character(),]])
    damage = 20
    roll = 10
    event = WoundCheckFailedEvent(character, damage, roll)
    listener = WoundCheckFailedListener()
    responses = list(listener.handle(character, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    # missing a wound check by 19 means 2 SW
    self.assertTrue(isinstance(response, SeriousWoundsDamageEvent))
    self.assertEqual(2, response.damage)
    # character's lw should be reset
    self.assertEqual(0, character.lw())


# TODO: test wound check succeeded listener


if (__name__ == '__main__'):
  unittest.main()

