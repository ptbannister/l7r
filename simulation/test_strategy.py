#!/usr/bin/env python3

#
# test_strategy.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator Strategy classes
#

import logging
import sys
import unittest

from simulation.actions import AttackAction
from simulation.character import Character
from simulation.context import EngineContext
from simulation.events import AttackDeclaredEvent, AttackRolledEvent, LightWoundsDamageEvent, NewPhaseEvent, TakeAttackActionEvent, TakeParryActionEvent, TakeSeriousWoundEvent, WoundCheckDeclaredEvent, WoundCheckRolledEvent, WoundCheckSucceededEvent
from simulation.log import logger
from simulation.roll_provider import TestRollProvider
from simulation.strategy import AttackStrategy, KeepLightWoundsStrategy, NeverParryStrategy, ParryStrategy, WoundCheckStrategy


# set up logging
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


def get_simple_groups():
  akodo = Character('Akodo')
  bayushi = Character('Bayushi')
  return [[akodo,], [bayushi,]]


class TestAttackStrategy(unittest.TestCase):
  def test_recommend(self):
    # set up characters and context
    akodo = Character('Akodo')
    akodo._actions = [1,]
    bayushi = Character('Bayushi')
    bayushi._actions = [2,]
    groups = [[akodo,], [bayushi,]]
    context = EngineContext(groups, round=1, phase=1)
    # construct strategy
    strategy = AttackStrategy()
    # play event on strategy in phase 1
    self.assertEqual(1, context.phase())
    recommendation = strategy.recommend(akodo, NewPhaseEvent(context.phase()), context)
    self.assertTrue(recommendation is not None)
    self.assertTrue(isinstance(recommendation, TakeAttackActionEvent))
    self.assertTrue(isinstance(recommendation.action, AttackAction))
    self.assertEqual(akodo, recommendation.action.subject())
    self.assertEqual(bayushi, recommendation.action.target())

  def test_recommend_no_action(self):
    # set up characters and context
    akodo = Character('Akodo')
    akodo._actions = [1, 2, 3]
    bayushi = Character('Bayushi')
    bayushi._actions = [2, 4, 6]
    groups = [[akodo,], [bayushi,]]
    context = EngineContext(groups)
    # construct strategy
    strategy = AttackStrategy()
    # play event on strategy in phase 0
    self.assertEqual(0, context.phase())
    recommendation = strategy.recommend(akodo, NewPhaseEvent(context.phase()), context)
    self.assertTrue(recommendation is None)


class TestKeepLightWoundsStrategy(unittest.TestCase):
  def test_keep_lw_small_hit(self):
    # set up character and wound check roll event
    character = Character()
    character.set_ring('water', 5)
    character.take_lw(10)
    context = EngineContext([[character,], [Character()]])
    context.load_probability_data()
    strategy = KeepLightWoundsStrategy()
    event = WoundCheckSucceededEvent(character, 10, 30)
    recommendation = strategy.recommend(character, event, context)
    # should not recommend taking SW for a small hit
    self.assertTrue(recommendation is None)

  def test_keep_lw_near_defeat(self):
    # set up character and wound check roll event
    character = Character()
    character.take_sw(3)
    character.take_lw(9001)
    context = EngineContext([[character,], [Character()]])
    strategy = KeepLightWoundsStrategy()
    event = WoundCheckSucceededEvent(character, 9001, 9002)
    recommendation = strategy.recommend(character, event, context)
    # should not recommend taking SW when one hit from defeat
    self.assertTrue(recommendation is None)

  def test_take_sw(self):
    # set up character and wound check roll event
    character = Character()
    character.take_lw(100)
    context = EngineContext([[character,], [Character()]])
    context.load_probability_data()
    strategy = KeepLightWoundsStrategy()
    event = WoundCheckSucceededEvent(character, 100, 101)
    recommendation = strategy.recommend(character, event, context)
    # should recommend taking SW when the next wound check looks dangerous
    self.assertTrue(isinstance(recommendation, TakeSeriousWoundEvent))
    self.assertEqual(1, recommendation.damage)


class TestParryStrategy(unittest.TestCase):
  def test_do_not_parry_miss(self):
    attacker = Character('attacker')
    target = Character('target')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    target.set_roll_provider(roll_provider)
    target.roll_initiative()
    context = EngineContext([[attacker,], [target,]], round=1, phase=1)
    strategy = ParryStrategy()
    attack = AttackAction(attacker, target)
    attack._attack_roll = 1
    event = AttackRolledEvent(attack, 1)
    recommendation = strategy.recommend(target, event, context)
    self.assertFalse(attack.is_hit())
    self.assertEqual(0, len(attack.parries_declared()))
    self.assertFalse(attack.parry_attempted())
    self.assertFalse(attack.parried())
    self.assertTrue(recommendation is None)

  def test_do_not_parry_for_enemies(self):
    shiba = Character('Shiba')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    shiba.set_roll_provider(roll_provider)
    shiba.roll_initiative()
    isawa = Character('Isawa')
    fu_leng = Character('Fu Leng')
    context = EngineContext([[shiba, isawa], [fu_leng,]], round=1, phase=1)
    strategy = ParryStrategy()
    attack = AttackAction(isawa, fu_leng)
    attack._attack_roll = 9001
    event = AttackRolledEvent(attack, 9001)
    recommendation = strategy.recommend(shiba, event, context)
    self.assertEqual(0, len(attack.parries_declared()))
    self.assertFalse(attack.parry_attempted())
    self.assertFalse(attack.parried())
    self.assertTrue(recommendation is None)

  def test_do_not_parry_small_attack(self):
    attacker = Character('attacker')
    target = Character('target')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    target.set_roll_provider(roll_provider)
    target.roll_initiative()
    context = EngineContext([[attacker,], [target,]], round=1, phase=1)
    strategy = ParryStrategy()
    attack = AttackAction(attacker, target)
    attack._attack_roll = 20
    event = AttackRolledEvent(attack, 20)
    recommendation = strategy.recommend(target, event, context)
    self.assertTrue(attack.is_hit())
    self.assertEqual(0, len(attack.parries_declared()))
    self.assertFalse(attack.parry_attempted())
    self.assertFalse(attack.parried())
    self.assertEqual(2, attack.calculate_extra_damage_dice())
    self.assertTrue(recommendation is None)

  def test_parry_big_hit(self):
    attacker = Character('attacker')
    attacker.take_sw(3)
    target = Character('target')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    target.set_roll_provider(roll_provider)
    target.roll_initiative()
    context = EngineContext([[attacker,], [target,]], round=1, phase=1)
    strategy = ParryStrategy()
    attack = AttackAction(attacker, target)
    attack._attack_roll = 9001
    event = AttackRolledEvent(attack, 9001)
    recommendation = strategy.recommend(target, event, context)
    self.assertTrue(attack.is_hit())
    self.assertTrue(isinstance(recommendation, TakeParryActionEvent))

  def test_parry_double_attack(self):
    attacker = Character('attacker')
    attacker.take_sw(3)
    target = Character('target')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    target.set_roll_provider(roll_provider)
    target.roll_initiative()
    context = EngineContext([[attacker,], [target,]], round=1, phase=1)
    strategy = ParryStrategy()
    attack = AttackAction(attacker, target, skill='double attack')
    attack._attack_roll = 25
    event = AttackRolledEvent(attack, 25)
    recommendation = strategy.recommend(target, event, context)
    self.assertTrue(attack.is_hit())
    self.assertTrue(isinstance(recommendation, TakeParryActionEvent))


class TestNeverParryStrategy(unittest.TestCase):
  def test_do_not_parry_big_attack(self):
    attacker = Character('attacker')
    target = Character('target')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    target.set_roll_provider(roll_provider)
    target.roll_initiative()
    context = EngineContext([[attacker,], [target,]], round=1, phase=1)
    strategy = NeverParryStrategy()
    attack = AttackAction(attacker, target)
    attack._attack_roll = 9001
    event = AttackRolledEvent(attack, 9001)
    recommendation = strategy.recommend(target, event, context)
    self.assertTrue(recommendation is None)

  def test_do_not_parry_double_attack(self):
    attacker = Character('attacker')
    target = Character('target')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    target.set_roll_provider(roll_provider)
    target.roll_initiative()
    context = EngineContext([[attacker,], [target,]], round=1, phase=1)
    strategy = NeverParryStrategy()
    attack = AttackAction(attacker, target, skill='double attack')
    attack._attack_roll = 30
    event = AttackRolledEvent(attack, 30)
    recommendation = strategy.recommend(target, event, context)
    self.assertTrue(recommendation is None)


class TestWoundCheckStrategy(unittest.TestCase):
  def test_declare_wound_check(self):
    # set up character and wound check roll event
    character = Character()
    character.take_lw(10)
    context = EngineContext([[character,], [Character(),]])
    context.load_probability_data()
    strategy = WoundCheckStrategy()
    event = LightWoundsDamageEvent(character, 10)
    recommendation = strategy.recommend(character, event, context)
    self.assertTrue(isinstance(recommendation, WoundCheckDeclaredEvent))
    self.assertEqual(0, recommendation.vp)


if (__name__ == '__main__'):
  unittest.main()

