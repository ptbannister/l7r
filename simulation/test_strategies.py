#!/usr/bin/env python3

#
# test_strategies.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator Strategy classes
#

import logging
import sys
import unittest

from simulation import events
from simulation.actions import AttackAction, DoubleAttackAction
from simulation.character import Character
from simulation.context import EngineContext
from simulation.groups import Group
from simulation.log import logger
from simulation.roll_provider import TestRollProvider
from simulation.strategies import BaseAttackStrategy, PlainAttackStrategy, KeepLightWoundsStrategy, NeverParryStrategy, ReluctantParryStrategy, WoundCheckStrategy


# set up logging
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


class TestBaseAttackStrategy(unittest.TestCase):
  def setUp(self):
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
    groups = [Group('attacker', attacker), Group('target', target)]
    # set up context
    context = EngineContext(groups, round=1, phase=1) 
    context.initialize()
    # set objects on test class
    self.attacker = attacker
    self.target = target
    self.context = context
    
  def test_get_expected_kept_damage_dice(self):
    # set up strategy
    strategy = BaseAttackStrategy()
    # use attack strategy to calculate expected damage
    # base skill roll params are 7k3, expected attack roll is 26, expected damage roll is 7k2
    self.assertEqual(2, strategy.get_expected_kept_damage_dice(self.attacker, self.target, 'attack', self.context, 0, 0))
    # spend 1 vp
    # skill roll params are 8k4, expected attack roll is 34, expected damage roll is 8k2
    self.assertEqual(2, strategy.get_expected_kept_damage_dice(self.attacker, self.target, 'attack', self.context, 0, 1))
    # spend 2 vp
    # skill roll params are 9k5, expected attack roll is 41, expected damage roll is 10k2
    self.assertEqual(2, strategy.get_expected_kept_damage_dice(self.attacker, self.target, 'attack', self.context, 0, 2))
    # spend 2 vp, 1 ap
    # skill roll params are 9k5+5, expected attack roll is 46, expected damage roll is 10k3
    self.assertEqual(3, strategy.get_expected_kept_damage_dice(self.attacker, self.target, 'attack', self.context, 1, 2))
    # spend 2 vp, 2 ap
    # skill roll params are 9k5+10, expected attack roll is 51, expected damage roll is 10k4
    self.assertEqual(4, strategy.get_expected_kept_damage_dice(self.attacker, self.target, 'attack', self.context, 2, 2))
    # try a high-fire character
    akodo = Character('Akodo')
    akodo._actions = [0,1,2,3,4]
    akodo.set_ring('fire', 5)
    akodo.set_skill('attack', 4)
    akodo.set_extra_rolled('attack', 1)
    akodo.knowledge().observe_tn_to_hit(self.target, 25)
    # base skill roll params are 10k5, expected attack roll is 44, expected damage roll is 10k4
    self.assertEqual(4, strategy.get_expected_kept_damage_dice(akodo, self.target, 'attack', self.context, 0, 0))
    # spend 1 vp, 0 ap
    # skill roll params are 10k7, expected attack roll is 53, expected damage roll is 10k6
    self.assertEqual(6, strategy.get_expected_kept_damage_dice(akodo, self.target, 'attack', self.context, 0, 1))
    # spend 0 vp, 1 ap
    # skill roll params are 10k5+5, expected attack roll is 49, expected damage roll is 10k5
    self.assertEqual(5, strategy.get_expected_kept_damage_dice(akodo, self.target, 'attack', self.context, 1, 0))

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
    # give attackers knowledge of target's TN to be hit
    weak_attacker.knowledge().observe_tn_to_hit(self.target, 25)
    strong_attacker.knowledge().observe_tn_to_hit(self.target, 25)
    # set up groups
    groups = [Group('attackers', [weak_attacker, strong_attacker]), Group('target', self.target)]
    # set up context
    context = EngineContext(groups, round=1, phase=1) 
    context.initialize()
    # use attack strategy to optimize attack
    strategy = PlainAttackStrategy()
    attack = strategy.optimize_attack(weak_attacker, self.target, 'attack', context)
    # weak attacker should not spend vp
    self.assertFalse(attack is None)
    self.assertEqual(self.target, attack.target())
    self.assertEqual(0, attack.vp())
    # strong attacker should spend 1 vp
    attack = strategy.optimize_attack(strong_attacker, self.target, 'attack', context)
    self.assertFalse(attack is None)
    self.assertEqual(self.target, attack.target())
    self.assertEqual(1, attack.vp())


class TestAttackStrategy(unittest.TestCase):
  def test_recommend(self):
    # set up characters and context
    akodo = Character('Akodo')
    akodo._actions = [1,]
    bayushi = Character('Bayushi')
    bayushi._actions = [2,]
    context = EngineContext([Group('Lion', akodo), Group('Scorpion', bayushi)], round=1, phase=1)
    context.initialize()
    # construct strategy
    strategy = PlainAttackStrategy()
    # play event on strategy in phase 1
    self.assertEqual(1, context.phase())
    responses = list(strategy.recommend(akodo, events.YourMoveEvent(akodo), context))
    self.assertEqual(2, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, events.SpendActionEvent))
    response = responses[1]
    self.assertTrue(isinstance(response, events.TakeAttackActionEvent))
    self.assertTrue(isinstance(response.action, AttackAction))
    self.assertEqual(akodo, response.action.subject())
    self.assertEqual(bayushi, response.action.target())

  def test_recommend_no_action(self):
    # set up characters and context
    akodo = Character('Akodo')
    akodo._actions = [1, 2, 3]
    bayushi = Character('Bayushi')
    bayushi._actions = [2, 4, 6]
    context = EngineContext([Group('Lion', akodo), Group('Scorpion', bayushi)])
    # construct strategy
    strategy = PlainAttackStrategy()
    # play event on strategy in phase 0
    self.assertEqual(0, context.phase())
    responses = list(strategy.recommend(akodo, events.YourMoveEvent(akodo), context))
    self.assertEqual(1, len(responses))
    self.assertTrue(isinstance(responses[0], events.NoActionEvent))


class TestKeepLightWoundsStrategy(unittest.TestCase):
  def setUp(self):
    # set up characters
    character = Character('subject')
    attacker = Character('attacker')
    # set up groups and context
    groups = [Group('subject', character), Group('attacker', attacker)]
    context = EngineContext(groups)
    context.initialize()
    self.character = character
    self.attacker = attacker
    self.context = context

  def test_keep_lw_small_hit(self):
    # give character a big wound check and a few LW
    self.character.set_ring('water', 5)
    self.character.take_lw(10)
    strategy = KeepLightWoundsStrategy()
    event = events.WoundCheckSucceededEvent(self.character, self.attacker, 10, 30)
    responses = list(strategy.recommend(self.character, event, self.context))
    # should not recommend taking SW for a small hit
    self.assertEqual([], responses)

  def test_keep_lw_near_defeat(self):
    # give character a lot of SW and LW
    self.character.take_sw(3)
    self.character.take_lw(9001)
    strategy = KeepLightWoundsStrategy()
    event = events.WoundCheckSucceededEvent(self.character, self.attacker, 9001, 9002)
    responses = list(strategy.recommend(self.character, event, self.context))
    # should not recommend taking SW when one hit from defeat
    self.assertEqual([], responses)

  def test_take_sw(self):
    # give character a lot of LW so they must take a SW
    self.character.take_lw(100)
    strategy = KeepLightWoundsStrategy()
    event = events.WoundCheckSucceededEvent(self.character, self.attacker, 100, 101)
    responses = list(strategy.recommend(self.character, event, self.context))
    # should recommend taking SW when the next wound check looks dangerous
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, events.TakeSeriousWoundEvent))
    self.assertEqual(1, response.damage)


class TestReluctantParryStrategy(unittest.TestCase):
  def setUp(self):
    # set up attacker
    attacker = Character('attacker')
    # set up target with actions
    target = Character('target')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    target.set_roll_provider(roll_provider)
    target.roll_initiative()
    # set up groups
    attacker_group = Group('attacker', attacker)
    target_group = Group('target', target)
    groups = [attacker_group, target_group]
    # set up context
    context = EngineContext(groups, round=1, phase=1)
    context.initialize()
    # set objects on instance
    self.attacker = attacker
    self.target = target
    self.context = context

  def test_do_not_parry_miss(self):
    # set up attack
    attack = AttackAction(self.attacker, self.target)
    attack.set_skill_roll(1)
    event = events.AttackRolledEvent(attack, 1)
    # get the recommendation
    strategy = ReluctantParryStrategy()
    responses = list(strategy.recommend(self.target, event, self.context))
    # should not try to parry a missed attack
    self.assertFalse(attack.is_hit())
    self.assertEqual(0, len(attack.parries_declared()))
    self.assertFalse(attack.parry_attempted())
    self.assertFalse(attack.parried())
    self.assertEqual([], responses)

  def test_do_not_parry_for_enemies(self):
    shiba = Character('Shiba')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    shiba.set_roll_provider(roll_provider)
    shiba.roll_initiative()
    isawa = Character('Isawa')
    fu_leng = Character('Fu Leng')
    # set up groups
    phoenix_group = Group('Phoenix', [shiba, isawa])
    shadowlands_group = Group('Shadowlands', fu_leng)
    groups = [phoenix_group, shadowlands_group]
    # set up context
    context = EngineContext(groups, round=1, phase=1)
    # set up attack 
    attack = AttackAction(isawa, fu_leng)
    attack.set_skill_roll(9001)
    event = events.AttackRolledEvent(attack, 9001)
    # get the recommendation
    strategy = ReluctantParryStrategy()
    responses = list(strategy.recommend(shiba, event, context))
    # shiba should not parry for fu leng
    self.assertEqual(0, len(attack.parries_declared()))
    self.assertFalse(attack.parry_attempted())
    self.assertFalse(attack.parried())
    self.assertEqual([], responses)

  def test_do_not_parry_small_attack(self):
    # set up attack
    attack = AttackAction(self.attacker, self.target)
    attack.set_skill_roll(20)
    event = events.AttackRolledEvent(attack, 20)
    # use the straevents.tegy
    strategy = ReluctantParryStrategy()
    responses = list(strategy.recommend(self.target, event, self.context))
    # should not parry a small attack
    self.assertTrue(attack.is_hit())
    self.assertEqual(0, len(attack.parries_declared()))
    self.assertFalse(attack.parry_attempted())
    self.assertFalse(attack.parried())
    self.assertEqual(2, attack.calculate_extra_damage_dice())
    self.assertEqual([], responses)

  def test_parry_big_hit(self):
    # make target near death so they will have to parry
    self.target.take_sw(3)
    # set up attack
    attack = AttackAction(self.attacker, self.target)
    attack.set_skill_roll(9001)
    event = events.AttackRolledEvent(attack, 9001)
    # use the strategy
    strategy = ReluctantParryStrategy()
    responses = list(strategy.recommend(self.target, event, self.context))
    # should parry a big hit
    self.assertTrue(attack.is_hit())
    self.assertEqual(2, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, events.SpendActionEvent))
    response = responses[1]
    self.assertTrue(isinstance(response, events.TakeParryActionEvent))

  def test_parry_double_attack(self):
    # make target near death so they will have to parry
    self.target.take_sw(3)
    # set up attack
    attack = DoubleAttackAction(self.attacker, self.target)
    attack.set_skill_roll(30)
    event = events.AttackRolledEvent(attack, 30)
    # use the strategy
    strategy = ReluctantParryStrategy()
    responses = list(strategy.recommend(self.target, event, self.context))
    # should parry a double attack
    self.assertTrue(attack.is_hit())
    self.assertEqual(2, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, events.SpendActionEvent))
    response = responses[1]
    self.assertTrue(isinstance(response, events.TakeParryActionEvent))


class TestNeverParryStrategy(unittest.TestCase):
  def setUp(self):
    # set up attacker
    attacker = Character('attacker')
    # set up target with actions
    target = Character('target')
    roll_provider = TestRollProvider()
    roll_provider.put_initiative_roll([1,1,1])
    target.set_roll_provider(roll_provider)
    target.roll_initiative()
    # set up groups
    attacker_group = Group('attacker', attacker)
    target_group = Group('target', target)
    groups = [attacker_group, target_group]
    # set up context
    context = EngineContext(groups, round=1, phase=1)
    # set objects on instance
    self.attacker = attacker
    self.target = target
    self.context = context

  def test_do_not_parry_big_attack(self):
    # set up attack
    attack = AttackAction(self.attacker, self.target)
    attack.set_skill_roll(9001)
    event = events.AttackRolledEvent(attack, 9001)
    # use the strategy
    strategy = NeverParryStrategy()
    responses = list(strategy.recommend(self.target, event, self.context))
    # should never parry
    self.assertEqual([], responses)

  def test_do_not_parry_double_attack(self):
    # set up attack
    attack = DoubleAttackAction(self.attacker, self.target)
    attack.set_skill_roll(30)
    event = events.AttackRolledEvent(attack, 30)
    # use the strategy
    strategy = NeverParryStrategy()
    responses = list(strategy.recommend(self.target, event, self.context))
    # should never parry
    self.assertEqual([], responses)


class TestWoundCheckStrategy(unittest.TestCase):
  def test_declare_wound_check(self):
    # set up character and wound check roll event
    character = Character('subject')
    attacker = Character('attacker')
    character.take_lw(10)
    context = EngineContext([Group('subject', character), Group('attacker', Character())])
    context.initialize()
    strategy = WoundCheckStrategy()
    event = events.LightWoundsDamageEvent(attacker, character, 10)
    responses = list(strategy.recommend(character, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, events.WoundCheckDeclaredEvent))
    self.assertEqual(0, response.vp)


if (__name__ == '__main__'):
  unittest.main()

