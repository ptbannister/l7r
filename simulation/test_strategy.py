#!/usr/bin/env python3

#
# test_strategy.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator Strategy classes
#

import logging
import sys
import unittest

from simulation.actions import AttackAction, DoubleAttackAction
from simulation.character import Character
from simulation.context import EngineContext
from simulation.events import AttackDeclaredEvent, AttackRolledEvent, LightWoundsDamageEvent, NewPhaseEvent, TakeAttackActionEvent, TakeParryActionEvent, TakeSeriousWoundEvent, WoundCheckDeclaredEvent, WoundCheckRolledEvent, WoundCheckSucceededEvent
from simulation.groups import Group
from simulation.log import logger
from simulation.roll_provider import TestRollProvider
from simulation.strategy import PlainAttackStrategy, KeepLightWoundsStrategy, NeverParryStrategy, ReluctantParryStrategy, WoundCheckStrategy


# set up logging
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


def get_simple_groups():
  akodo = Character('Akodo')
  bayushi = Character('Bayushi')
  return [[akodo,], [bayushi,]]


class TestAttackStrategy(unittest.TestCase):
  def test_get_expected_kept_damage_dice(self):
    # set up characters
    attacker = Character('attacker')
    attacker._actions = [1,]
    attacker.set_ring('fire', 3)
    attacker.set_skill('attack', 3)
    attacker.set_extra_rolled('attack', 1)
    target = Character('target')
    target._actions = [2,]
    target.set_skill('parry', 4)
    # give attacker knowledge of target's TN to be hit
    attacker.knowledge().observe_tn_to_hit(target, 25)
    # set up groups
    groups = [Group([attacker]), Group([target])]
    # set up context
    context = EngineContext(groups, round=1, phase=1) 
    context.load_probability_data()
    # use attack strategy to calculate expected damage
    strategy =PlainAttackStrategy()
    # base skill roll params are 7k3, expected attack roll is 26, expected damage roll is 7k2
    self.assertEqual(2, strategy._get_expected_kept_damage_dice(attacker, context, target, 'attack', 0, 0))
    # spend 1 vp
    # skill roll params are 8k4, expected attack roll is 34, expected damage roll is 8k2
    self.assertEqual(2, strategy._get_expected_kept_damage_dice(attacker, context, target, 'attack', 0, 1))
    # spend 2 vp
    # skill roll params are 9k5, expected attack roll is 41, expected damage roll is 10k2
    self.assertEqual(2, strategy._get_expected_kept_damage_dice(attacker, context, target, 'attack', 0, 2))
    # spend 2 vp, 1 ap
    # skill roll params are 9k5+5, expected attack roll is 46, expected damage roll is 10k3
    self.assertEqual(3, strategy._get_expected_kept_damage_dice(attacker, context, target, 'attack', 1, 2))
    # spend 2 vp, 2 ap
    # skill roll params are 9k5+10, expected attack roll is 51, expected damage roll is 10k4
    self.assertEqual(4, strategy._get_expected_kept_damage_dice(attacker, context, target, 'attack', 2, 2))
    # try a high-fire character
    akodo = Character('Akodo')
    akodo._actions = [0,1,2,3,4]
    akodo.set_ring('fire', 5)
    akodo.set_skill('attack', 4)
    akodo.set_extra_rolled('attack', 1)
    akodo.knowledge().observe_tn_to_hit(target, 25)
    # base skill roll params are 10k5, expected attack roll is 44, expected damage roll is 10k4
    self.assertEqual(4, strategy._get_expected_kept_damage_dice(akodo, context, target, 'attack', 0, 0))
    # spend 1 vp, 0 ap
    # skill roll params are 10k7, expected attack roll is 53, expected damage roll is 10k6
    self.assertEqual(6, strategy._get_expected_kept_damage_dice(akodo, context, target, 'attack', 0, 1))
    # spend 1 ap, 0 vp
    # skill roll params are 10k5+5, expected attack roll is 49, expected damage roll is 10k5
    self.assertEqual(5, strategy._get_expected_kept_damage_dice(akodo, context, target, 'attack', 1, 0))

  def test_optimize_attack(self):
    # set up characters
    weak_attacker = Character('weak attacker')
    weak_attacker._actions = [1,]
    weak_attacker.set_ring('fire', 3)
    weak_attacker.set_skill('attack', 3)
    weak_attacker.set_extra_rolled('attack', 1)
    strong_attacker = Character('strong attacker')
    strong_attacker._actions = [1,]
    strong_attacker.set_ring('fire', 5)
    strong_attacker.set_skill('attack', 4)
    strong_attacker.set_extra_rolled('attack', 1)
    target = Character('target')
    target._actions = [2,]
    target.set_skill('parry', 4)
    # give attackers knowledge of target's TN to be hit
    weak_attacker.knowledge().observe_tn_to_hit(target, 25)
    strong_attacker.knowledge().observe_tn_to_hit(target, 25)
    # set up groups
    groups = [Group([weak_attacker, strong_attacker]), Group([target])]
    # set up context
    context = EngineContext(groups, round=1, phase=1) 
    context.load_probability_data()
    # use attack strategy to optimize attack
    strategy =PlainAttackStrategy()
    attack = strategy._optimize_attack(weak_attacker, context, target)
    # weak attacker should not spend ap or vp
    self.assertFalse(attack is None)
    self.assertEqual(target, attack.target())
    self.assertEqual(0, attack.ap())
    self.assertEqual(0, attack.vp())
    # strong attacker should spend 1 vp
    attack = strategy._optimize_attack(strong_attacker, context, target)
    self.assertFalse(attack is None)
    self.assertEqual(target, attack.target())
    self.assertEqual(0, attack.ap())
    self.assertEqual(1, attack.vp())

  def test_recommend(self):
    # set up characters and context
    akodo = Character('Akodo')
    akodo._actions = [1,]
    bayushi = Character('Bayushi')
    bayushi._actions = [2,]
    context = EngineContext([Group([akodo]), Group([bayushi])], round=1, phase=1)
    context.load_probability_data()
    # construct strategy
    strategy =PlainAttackStrategy()
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
    context = EngineContext([Group([akodo]), Group([bayushi])])
    # construct strategy
    strategy =PlainAttackStrategy()
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
    context = EngineContext([Group([character]), Group([Character()])])
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
    context = EngineContext([Group([character]), Group([Character()])])
    strategy = KeepLightWoundsStrategy()
    event = WoundCheckSucceededEvent(character, 9001, 9002)
    recommendation = strategy.recommend(character, event, context)
    # should not recommend taking SW when one hit from defeat
    self.assertTrue(recommendation is None)

  def test_take_sw(self):
    # set up character and wound check roll event
    character = Character()
    character.take_lw(100)
    context = EngineContext([Group([character]), Group([Character()])])
    context.load_probability_data()
    strategy = KeepLightWoundsStrategy()
    event = WoundCheckSucceededEvent(character, 100, 101)
    recommendation = strategy.recommend(character, event, context)
    # should recommend taking SW when the next wound check looks dangerous
    self.assertTrue(isinstance(recommendation, TakeSeriousWoundEvent))
    self.assertEqual(1, recommendation.damage)


class TestReluctantParryStrategy(unittest.TestCase):
  def test_do_not_parry_miss(self):
    attacker = Character('attacker')
    target = Character('target')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    target.set_roll_provider(roll_provider)
    target.roll_initiative()
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    groups = [attacker_group, target_group]
    # set up context
    context = EngineContext(groups, round=1, phase=1)
    # set up attack
    attack = AttackAction(attacker, target)
    attack._attack_roll = 1
    event = AttackRolledEvent(attack, 1)
    # get the recommendation
    strategy = ReluctantParryStrategy()
    recommendation = strategy.recommend(target, event, context)
    # should not try to parry a missed attack
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
    # set up groups
    phoenix_group = Group([shiba, isawa])
    shadowlands_group = Group([fu_leng])
    groups = [phoenix_group, shadowlands_group]
    # set up context
    context = EngineContext(groups, round=1, phase=1)
    # set up attack 
    attack = AttackAction(isawa, fu_leng)
    attack._attack_roll = 9001
    event = AttackRolledEvent(attack, 9001)
    # get the recommendation
    strategy = ReluctantParryStrategy()
    recommendation = strategy.recommend(shiba, event, context)
    # shiba should not parry for fu leng
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
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    groups = [attacker_group, target_group]
    # set up context
    context = EngineContext(groups, round=1, phase=1)
    context.load_probability_data()
    # set up attack
    attack = AttackAction(attacker, target)
    attack._attack_roll = 20
    event = AttackRolledEvent(attack, 20)
    # use the strategy
    strategy = ReluctantParryStrategy()
    recommendation = strategy.recommend(target, event, context)
    # should not parry a small attack
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
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    groups = [attacker_group, target_group]
    # set up context
    context = EngineContext(groups, round=1, phase=1)
    context.load_probability_data()
    # set up attack
    attack = AttackAction(attacker, target)
    attack._attack_roll = 9001
    event = AttackRolledEvent(attack, 9001)
    # use the strategy
    strategy = ReluctantParryStrategy()
    recommendation = strategy.recommend(target, event, context)
    # should parry a big hit
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
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    groups = [attacker_group, target_group]
    # set up context
    context = EngineContext(groups, round=1, phase=1)
    context.load_probability_data()
    # set up attack
    attack = DoubleAttackAction(attacker, target)
    attack._attack_roll = 25
    event = AttackRolledEvent(attack, 25)
    # use the strategy
    strategy = ReluctantParryStrategy()
    recommendation = strategy.recommend(target, event, context)
    # should parry a double attack
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
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    groups = [attacker_group, target_group]
    # set up context
    context = EngineContext(groups, round=1, phase=1)
    # set up attack
    attack = AttackAction(attacker, target)
    attack._attack_roll = 9001
    event = AttackRolledEvent(attack, 9001)
    # use the strategy
    strategy = NeverParryStrategy()
    recommendation = strategy.recommend(target, event, context)
    # should never parry
    self.assertTrue(recommendation is None)

  def test_do_not_parry_double_attack(self):
    attacker = Character('attacker')
    target = Character('target')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    target.set_roll_provider(roll_provider)
    target.roll_initiative()
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    groups = [attacker_group, target_group]
    # set up context
    context = EngineContext(groups, round=1, phase=1)
    # set up attack
    attack = DoubleAttackAction(attacker, target)
    attack._attack_roll = 30
    event = AttackRolledEvent(attack, 30)
    # use the strategy
    strategy = NeverParryStrategy()
    recommendation = strategy.recommend(target, event, context)
    # should never parry
    self.assertTrue(recommendation is None)


class TestWoundCheckStrategy(unittest.TestCase):
  def test_declare_wound_check(self):
    # set up character and wound check roll event
    character = Character()
    character.take_lw(10)
    context = EngineContext([Group([character]), Group([Character()])])
    context.load_probability_data()
    strategy = WoundCheckStrategy()
    event = LightWoundsDamageEvent(character, 10)
    recommendation = strategy.recommend(character, event, context)
    self.assertTrue(isinstance(recommendation, WoundCheckDeclaredEvent))
    self.assertEqual(0, recommendation.vp)


if (__name__ == '__main__'):
  unittest.main()

