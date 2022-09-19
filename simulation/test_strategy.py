#!/usr/bin/env python3

#
# test_strategy.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator Strategy classes
#

import unittest

from simulation.actions import AttackAction
from simulation.character import Character
from simulation.context import EngineContext
from simulation.events import AttackDeclaredEvent, LightWoundsDamageEvent, NewPhaseEvent, TakeAttackActionEvent, TakeSeriousWoundEvent, WoundCheckDeclaredEvent, WoundCheckRolledEvent, WoundCheckSucceededEvent
from simulation.strategy import AttackStrategy, KeepLightWoundsStrategy, WoundCheckStrategy

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
  def test_take_sw(self):
    # set up character and wound check roll event
    character = Character()
    character.take_lw(10)
    context = EngineContext([[character,], [Character()]])
    strategy = KeepLightWoundsStrategy()
    event = WoundCheckSucceededEvent(character, 10, 100)
    recommendation = strategy.recommend(character, event, context)
    self.assertTrue(isinstance(recommendation, TakeSeriousWoundEvent))
    self.assertEqual(1, recommendation.amount)


class TestWoundCheckStrategy(unittest.TestCase):
  def test_declare_wound_check(self):
    # set up character and wound check roll event
    character = Character()
    character.take_lw(10)
    context = EngineContext([[character,], [Character()]])
    strategy = WoundCheckStrategy()
    event = LightWoundsDamageEvent(character, 10)
    recommendation = strategy.recommend(character, event, context)
    self.assertTrue(isinstance(recommendation, WoundCheckDeclaredEvent))
    self.assertEqual(0, recommendation.vp)


if (__name__ == '__main__'):
  unittest.main()

