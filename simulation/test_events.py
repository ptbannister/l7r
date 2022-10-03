#!/usr/bin/env python3

#
# test_events.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator events module
#

import logging
import sys
import unittest

from simulation.actions import AttackAction, ParryAction
from simulation.character import Character
from simulation.context import EngineContext
from simulation.engine import CombatEngine
from simulation import events
from simulation.groups import Group
from simulation.log import logger
from simulation.roll_provider import TestRollProvider
from simulation.strategies import AlwaysParryStrategy, NeverParryStrategy, PlainAttackStrategy, ReluctantParryStrategy


# set up logging
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


class TestTakeAttackActionEvent(unittest.TestCase):
  def test_run_hit(self):
    # set up characters
    attacker = Character('attacker')
    attacker.set_ring('fire', 5)
    attacker.set_skill('attack', 4)
    attacker._actions = [1]
    target = Character('target')
    target.set_parry_strategy(NeverParryStrategy())
    target.set_ring('air', 5)
    target.set_skill('parry', 5)
    target._actions = [1]
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    # rig the attack roll to hit by 1
    attacker_roll_provider = TestRollProvider()
    attacker_roll_provider.put_skill_roll('attack', 31)
    attacker_roll_provider.put_damage_roll(15)
    attacker.set_roll_provider(attacker_roll_provider)
    # rig the wound check to succeed
    target_roll_provider = TestRollProvider()
    target_roll_provider.put_wound_check_roll(25)
    target.set_roll_provider(target_roll_provider)
    # set up attack
    attack = AttackAction(attacker, target)
    # set up engine
    context = EngineContext([attacker_group, target_group])
    context.load_probability_data()
    engine = CombatEngine(context)
    # run the event
    event = events.TakeAttackActionEvent(attack)
    # run the attack
    engine.event(event)
    # assert expected attack action state
    self.assertEqual(31, attack._attack_roll)
    self.assertEqual([], attack.parries_declared())
    self.assertFalse(attack.parried())
    self.assertTrue(attack.is_hit())
    self.assertEqual(0, attack.calculate_extra_damage_dice())
    self.assertEqual(15, attack._damage_roll)
    # assert expected event history
    history = engine.get_history()
    first_event = history.pop(0)
    self.assertTrue(isinstance(first_event, events.TakeAttackActionEvent))
    second_event = history.pop(0)
    self.assertTrue(isinstance(second_event, events.AttackDeclaredEvent))
    third_event = history.pop(0)
    self.assertTrue(isinstance(third_event, events.AttackRolledEvent))
    self.assertEqual(31, third_event.roll)
    fourth_event = history.pop(0)
    self.assertTrue(isinstance(fourth_event, events.AttackSucceededEvent))
    fifth_event = engine.get_history().pop(0)
    self.assertTrue(isinstance(fifth_event, events.LightWoundsDamageEvent))
    self.assertEqual(target, fifth_event.target)
    self.assertEqual(15, fifth_event.damage)

  def test_run_miss(self):
    attacker = Character('attacker')
    attacker.set_ring('fire', 5)
    attacker.set_skill('attack', 4)
    attacker._actions = [1]
    target = Character('target')
    target.set_parry_strategy(NeverParryStrategy())
    target.set_ring('air', 5)
    target.set_skill('parry', 5)
    target._actions = [1]
    # rig the attack roll to miss by 1
    attacker_roll_provider = TestRollProvider()
    attacker_roll_provider.put_skill_roll('attack', 29)
    attacker.set_roll_provider(attacker_roll_provider)
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    # set up attack
    attack = AttackAction(attacker, target)
    # set up engine
    context = EngineContext([attacker_group, target_group], round=1, phase=1)
    context.load_probability_data()
    engine = CombatEngine(context)
    # run the event
    event = events.TakeAttackActionEvent(attack)
    # run the attack
    engine.event(event)
    # assert expected attack action state
    self.assertEqual(29, attack._attack_roll)
    self.assertEqual([], attack.parries_declared())
    self.assertFalse(attack.parried())
    self.assertFalse(attack.is_hit())
    self.assertEqual
    # assert expected event history
    history = engine.get_history()
    first_event = history.pop(0)
    self.assertTrue(isinstance(first_event, events.TakeAttackActionEvent))
    second_event = history.pop(0)
    self.assertTrue(isinstance(second_event, events.AttackDeclaredEvent))
    third_event = history.pop(0)
    self.assertTrue(isinstance(third_event, events.AttackRolledEvent))
    self.assertEqual(29, third_event.roll)
    fourth_event = history.pop(0)
    self.assertTrue(isinstance(fourth_event, events.AttackFailedEvent))

  def test_run_failed_parry(self):
    attacker = Character('attacker')
    attacker.set_ring('fire', 5)
    attacker.set_skill('attack', 4)
    attacker._actions = [1]
    target = Character('target')
    target.set_ring('air', 5)
    target.set_skill('parry', 5)
    target._actions = [1]
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    # rig the attack roll to hit by 20 and the damage roll to be small
    attacker_roll_provider = TestRollProvider()
    attacker_roll_provider.put_skill_roll('attack', 50)
    attacker_roll_provider.put_damage_roll(15)
    attacker.set_roll_provider(attacker_roll_provider)
    # rig the parry to fail and the wound check to succeed
    target_roll_provider = TestRollProvider()
    target_roll_provider.put_skill_roll('parry', 49)
    target_roll_provider.put_wound_check_roll(25)
    target.set_roll_provider(target_roll_provider)
    # set up engine and context
    context = EngineContext([attacker_group, target_group], round=1, phase=1)
    context.load_probability_data()
    engine = CombatEngine(context)
    # set up an attack action
    attack = AttackAction(attacker, target)
    # run the event
    event = events.TakeAttackActionEvent(attack)
    engine.event(event)
    # assert expected attack action state
    self.assertEqual(50, attack._attack_roll)
    self.assertEqual(1, len(attack._parries_declared))
    self.assertEqual([], attack._parries_predeclared)
    self.assertFalse(attack.parried())
    self.assertTrue(attack.parry_attempted())
    self.assertTrue(attack.is_hit())
    self.assertEqual(0, attack.calculate_extra_damage_dice())
    self.assertEqual(15, attack._damage_roll)
    # assert expected event history
    history = engine.get_history()
    first_event = history.pop(0)
    self.assertTrue(isinstance(first_event, events.TakeAttackActionEvent))
    second_event = history.pop(0)
    self.assertTrue(isinstance(second_event, events.AttackDeclaredEvent))
    third_event = history.pop(0)
    self.assertTrue(isinstance(third_event, events.AttackRolledEvent))
    self.assertEqual(50, third_event.roll)
    fourth_event = history.pop(0)
    self.assertTrue(isinstance(fourth_event, events.TakeParryActionEvent))
    fifth_event = history.pop(0)
    self.assertTrue(isinstance(fifth_event, events.ParryDeclaredEvent))
    self.assertEqual(target, fifth_event.action.subject())
    self.assertEqual(attacker, fifth_event.action.target())
    sixth_event = history.pop(0)
    self.assertTrue(isinstance(sixth_event, events.ParryRolledEvent))
    self.assertEqual(target, sixth_event.action.subject())
    self.assertEqual(attacker, sixth_event.action.target())
    self.assertEqual(49, sixth_event.roll)
    self.assertFalse(sixth_event.action.is_success())
    seventh_event = history.pop(0)
    self.assertTrue(isinstance(seventh_event, events.ParryFailedEvent))
    eighth_event = history.pop(0)
    self.assertTrue(isinstance(eighth_event, events.AttackSucceededEvent))
    ninth_event = engine.get_history().pop(0)
    self.assertTrue(isinstance(ninth_event, events.LightWoundsDamageEvent))
    self.assertEqual(target, ninth_event.target)
    self.assertEqual(15, ninth_event.damage)

  def test_run_successful_parry(self):
    attacker = Character('attacker')
    attacker.set_ring('fire', 5)
    attacker.set_skill('attack', 4)
    attacker.set_strategy('attack', PlainAttackStrategy())
    attacker._actions = [1]
    target = Character('target')
    target.set_ring('air', 5)
    target.set_skill('parry', 5)
    target.set_strategy('parry', AlwaysParryStrategy())
    target._actions = [1]
    # rig the attack roll to hit by 20
    attacker_roll_provider = TestRollProvider()
    attacker_roll_provider.put_skill_roll('attack', 50)
    attacker.set_roll_provider(attacker_roll_provider)
    # rig the parry roll to succeed by 1
    target_roll_provider = TestRollProvider()
    target_roll_provider.put_skill_roll('parry', 51)
    target.set_roll_provider(target_roll_provider)
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    # set up engine and context
    context = EngineContext([attacker_group, target_group], round=1, phase=1)
    context.load_probability_data()
    engine = CombatEngine(context)
    # set up an attack action
    attack = AttackAction(attacker, target)
    # run the event
    event = events.TakeAttackActionEvent(attack)
    engine.event(event)
    # assert expected attack action state
    self.assertEqual(50, attack._attack_roll)
    self.assertTrue(attack.parried())
    self.assertTrue(attack.parry_attempted())
    self.assertFalse(attack.is_hit())
    # assert expected event history
    history = engine.get_history()
    first_event = history.pop(0)
    self.assertTrue(isinstance(first_event, events.TakeAttackActionEvent))
    second_event = history.pop(0)
    self.assertTrue(isinstance(second_event, events.AttackDeclaredEvent))
    third_event = history.pop(0)
    self.assertTrue(isinstance(third_event, events.AttackRolledEvent))
    self.assertEqual(50, third_event.roll)
    fourth_event = history.pop(0)
    self.assertTrue(isinstance(fourth_event, events.TakeParryActionEvent))
    fifth_event = history.pop(0)
    self.assertTrue(isinstance(fifth_event, events.ParryDeclaredEvent))
    self.assertEqual(target, fifth_event.action.subject())
    self.assertEqual(attacker, fifth_event.action.target())
    sixth_event = history.pop(0)
    self.assertTrue(isinstance(sixth_event, events.ParryRolledEvent))
    self.assertEqual(target, sixth_event.action.subject())
    self.assertEqual(attacker, sixth_event.action.target())
    self.assertEqual(51, sixth_event.roll)
    self.assertTrue(sixth_event.action.is_success())
    seventh_event = history.pop(0)
    self.assertTrue(isinstance(seventh_event, events.ParrySucceededEvent))
    eighth_event = history.pop(0)
    self.assertTrue(isinstance(eighth_event, events.AttackFailedEvent))
    self.assertEqual(0, len(history))


class TestTakeParryActionEvent(unittest.TestCase):
  def test_run_parry(self):
    attacker = Character('attacker')
    attacker.set_ring('fire', 5)
    attacker.set_skill('attack', 4)
    attacker._actions = [1]
    target = Character('target')
    target.set_ring('air', 5)
    target.set_skill('parry', 5)
    target._actions = [1]
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    # set up engine and context
    context = EngineContext([attacker_group, target_group], round=1, phase=1)
    context.load_probability_data()
    engine = CombatEngine(context)
    # set up an attack that hit by 20
    attack = AttackAction(attacker, target)
    attack._attack_roll = 50
    # set up the parry action
    parry = ParryAction(target, attacker, attack)
    # rig the parry roll to succeed by 1
    target_roll_provider = TestRollProvider()
    target_roll_provider.put_skill_roll('parry', 51)
    target.set_roll_provider(target_roll_provider)
    # run the event
    event = events.TakeParryActionEvent(parry)
    engine.event(event)
    # assert expected parry action state
    self.assertEqual(51, parry._parry_roll)
    self.assertTrue(parry.is_success())
    # assert expected attack action state
    self.assertTrue(attack.parried())
    self.assertTrue(attack.parry_attempted())
    self.assertFalse(attack.is_hit())
    # assert expected event history
    history = engine.get_history()
    first_event = history.pop(0)
    self.assertTrue(isinstance(first_event, events.TakeParryActionEvent))
    second_event = history.pop(0)
    self.assertTrue(isinstance(second_event, events.ParryDeclaredEvent))
    third_event = history.pop(0)
    self.assertTrue(isinstance(third_event, events.ParryRolledEvent))
    self.assertEqual(target, third_event.action.subject())
    self.assertEqual(attacker, third_event.action.target())
    self.assertEqual(51, third_event.roll)
    fourth_event = history.pop(0)
    self.assertTrue(isinstance(fourth_event, events.ParrySucceededEvent))

  def test_run_failed_parry(self):
    attacker = Character('attacker')
    attacker.set_ring('fire', 5)
    attacker.set_skill('attack', 4)
    attacker._actions = [1]
    target = Character('target')
    target.set_ring('air', 5)
    target.set_skill('parry', 5)
    target._actions = [1]
    # set up groups
    attacker_group = Group([attacker])
    target_group = Group([target])
    # set up engine and context
    context = EngineContext([attacker_group, target_group], round=1, phase=1)
    context.load_probability_data()
    engine = CombatEngine(context)
    # set up an attack that hit by 20
    attack = AttackAction(attacker, target)
    attack._attack_roll = 50
    # set up the parry action
    parry = ParryAction(target, attacker, attack)
    # rig the parry roll to fail by 1
    target_roll_provider = TestRollProvider()
    target_roll_provider.put_skill_roll('parry', 49)
    target.set_roll_provider(target_roll_provider)
    # run the event
    event = events.TakeParryActionEvent(parry)
    engine.event(event)
    # assert expected parry action state
    self.assertEqual(49, parry._parry_roll)
    self.assertFalse(parry.is_success())
    # assert expected attack action state
    self.assertFalse(attack.parried())
    self.assertTrue(attack.parry_attempted())
    self.assertTrue(attack.is_hit())
    self.assertEqual(0, attack.calculate_extra_damage_dice())
    # assert expected event history
    history = engine.get_history()
    first_event = history.pop(0)
    self.assertTrue(isinstance(first_event, events.TakeParryActionEvent))
    second_event = history.pop(0)
    self.assertTrue(isinstance(second_event, events.ParryDeclaredEvent))
    third_event = history.pop(0)
    self.assertTrue(isinstance(third_event, events.ParryRolledEvent))
    self.assertEqual(target, third_event.action.subject())
    self.assertEqual(attacker, third_event.action.target())
    self.assertEqual(49, third_event.roll)
    fourth_event = history.pop(0)
    self.assertTrue(isinstance(fourth_event, events.ParryFailedEvent))

