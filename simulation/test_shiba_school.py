#!/usr/bin/env python3

#
# test_shiba_school.py
#
# Unit tests for Shiba Bushi School classes.
#

import logging
import sys
import unittest

from simulation import actions, events, shiba_school
from simulation.character import Character
from simulation.character_builder import CharacterBuilder
from simulation.context import EngineContext
from simulation.engine import CombatEngine
from simulation.groups import Group
from simulation.log import logger
from simulation.roll_provider import TestRollProvider

# set up logging
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


class TestShibaActionFactory(unittest.TestCase):
  def test_get_parry(self):
    shiba = Character('Shiba')
    attacker = Character('attacker')
    factory = shiba_school.ShibaActionFactory()
    attack = actions.AttackAction(attacker, shiba, 'attack')
    parry = factory.get_parry_action(shiba, attacker, attack, 'parry')
    self.assertTrue(isinstance(parry, shiba_school.ShibaParryAction))
    self.assertEqual(shiba, parry.subject())
    self.assertEqual(attacker, parry.target())


class TestShibaParryAction(unittest.TestCase):
  def test_no_parry_other_penalty(self):
    shiba = Character('Shiba')
    attacker = Character('attacker')
    target = Character('target')
    attack = actions.AttackAction(attacker, target, 'attack')
    parry = shiba_school.ShibaParryAction(shiba, attacker, attack, 'parry')
    # rig shiba's parry roll
    roll_provider = TestRollProvider()
    roll_provider.put_skill_roll('parry', 50)
    shiba.set_roll_provider(roll_provider)
    # assert the parry action does not impose the -10 penalty
    skill_roll = parry.roll_parry()
    self.assertEqual(skill_roll, 50)


class TestShibaParrySucceededListener(unittest.TestCase):
  def setUp(self):
    # set up characters
    shiba = Character('Shiba')
    shiba.set_skill('attack', 4)
    shiba.set_skill('parry', 5)
    attacker = Character('attacker')
    attacker.set_skill('parry', 5)
    # set up context
    groups = [Group('Shiba', shiba), Group('attacker', attacker)]
    context = EngineContext(groups)
    # set instances on test case
    self.attacker = attacker
    self.shiba = shiba
    self.context = context

  def test_handle_parry_succeeded(self):
    # set up attack action
    attack = actions.AttackAction(self.attacker, self.shiba, 'attack')
    attack.set_skill_roll(45)
    # set up parry action
    parry = shiba_school.ShibaParryAction(self.shiba, self.attacker, attack, 'parry')
    parry.set_skill_roll(51)
    # set up parry succeeded event
    event = events.ParrySucceededEvent(parry)
    # play parry succeeded event on listener
    listener = shiba_school.ShibaParrySucceededListener()
    responses = list([response for response in listener.handle(self.shiba, event, self.context)])
    # should get one response: AddModifierEvent
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, events.AddModifierEvent))
    # should add a penalty to self.attacker's TN to be hit
    modifier = response.modifier
    self.assertEqual(self.attacker, modifier.subject())
    self.assertEqual(-6, modifier.adjustment())

  def test_run_parry_engine(self):
    # build Shiba as a 5th Dan character
    school = shiba_school.ShibaBushiSchool()
    builder = CharacterBuilder(9001) \
      .with_name('Shiba') \
      .with_school(school) \
      .buy_skill('attack', 4) \
      .buy_skill('parry', 5)
    for skill in school.school_knacks():
      builder.buy_skill(skill, 5)
    self.shiba = builder.build()
    groups = [Group('Shiba', self.shiba), Group('attacker', self.attacker)]
    self.context = EngineContext(groups, round=1, phase=1)
    self.context.initialize()
    # set up attack
    attack = actions.AttackAction(self.attacker, self.shiba, 'attack')
    attack.set_skill_roll(45)
    # set up parry
    parry = shiba_school.ShibaParryAction(self.shiba, self.attacker, attack, 'parry')
    take_action_event = shiba_school.ShibaTakeParryEvent(parry)
    # rig parry and damage rolls
    roll_provider = TestRollProvider()
    roll_provider.put_skill_roll('parry', 51)
    roll_provider.put_damage_roll(9)
    self.shiba.set_roll_provider(roll_provider)
    # set up engine
    engine = CombatEngine(self.context)
    # play parry event
    engine.event(take_action_event)
    # assert expected parry state
    self.assertTrue(parry.is_success())
    self.assertEqual(56, parry.skill_roll())
    # assert expected attack state
    self.assertFalse(attack.is_hit())
    self.assertTrue(attack.parry_attempted())
    self.assertTrue(attack.parried())
    # assert expected damage roll parameters
    self.assertEqual((8, 1), roll_provider.pop_observed_params('damage'))
    # assert attacker has expected modifier to tn to be hit
    self.assertEqual(-11, self.attacker.modifier(None, 'tn to hit'))
    self.assertEqual(19, self.attacker.tn_to_hit())
    # assert expected event history
    history = engine.history()
    # take_parry
    first_event = history.pop(0)
    self.assertTrue(isinstance(first_event, shiba_school.ShibaTakeParryEvent))
    # parry_declared
    second_event = history.pop(0)
    self.assertTrue(isinstance(second_event, events.ParryDeclaredEvent))
    # parry_rolled
    third_event = history.pop(0)
    self.assertTrue(isinstance(third_event, events.ParryRolledEvent))
    # parry_succeeded
    fourth_event = history.pop(0)
    self.assertTrue(isinstance(fourth_event, events.ParrySucceededEvent))
    # add_modifier
    fifth_event = history.pop(0)
    self.assertTrue(isinstance(fifth_event, events.AddModifierEvent))
    # lw_damage
    sixth_event = history.pop(0)
    self.assertTrue(isinstance(sixth_event, events.LightWoundsDamageEvent))


class TestShibaTakeParryEvent(unittest.TestCase):
  def setUp(self):
    shiba = Character('Shiba')
    shiba.set_skill('attack', 3)
    attacker = Character('attacker')
    attack = actions.AttackAction(attacker, shiba, 'attack')
    attack.set_skill_roll(50)
    parry = shiba_school.ShibaParryAction(shiba, attacker, attack, 'parry')
    take_action_event = shiba_school.ShibaTakeParryEvent(parry)
    groups = [Group('Phoenix', shiba), Group('attacker', attacker)]
    context = EngineContext(groups, round=1, phase=1)
    context.initialize()
    self.shiba = shiba
    self.attacker = attacker
    self.attack = attack
    self.context = context
    self.parry = parry
    self.take_action_event = take_action_event

  def test_damage_parry_failed(self):
    # set up engine
    engine = CombatEngine(self.context)
    # rig shiba's rolls
    roll_provider = TestRollProvider()
    roll_provider.put_skill_roll('parry', 44)
    roll_provider.put_damage_roll(10)
    self.shiba.set_roll_provider(roll_provider)
    # play parry action
    engine.event(self.take_action_event)
    # assert expected parry action state
    self.assertEqual(44, self.parry.skill_roll())
    self.assertFalse(self.parry.is_success())
    # assert expected attack action state
    self.assertTrue(self.attack.is_hit())
    self.assertFalse(self.attack.parried())
    self.assertTrue(self.attack.parry_attempted())
    # assert expected damage roll params
    observed_damage_params = roll_provider.pop_observed_params('damage')
    self.assertEqual((6, 1), observed_damage_params)
    # assert expected event history
    history = engine.history()
    # take_parry
    first_event = history.pop(0)
    self.assertTrue(isinstance(first_event, shiba_school.ShibaTakeParryEvent))
    # parry_declared
    second_event = history.pop(0)
    self.assertTrue(isinstance(second_event, events.ParryDeclaredEvent))
    # parry_rolled
    third_event = history.pop(0)
    self.assertTrue(isinstance(third_event, events.ParryRolledEvent))
    self.assertEqual(44, third_event.roll)
    # parry_failed
    fourth_event = history.pop(0)
    self.assertTrue(isinstance(fourth_event, events.ParryFailedEvent))
    # lw_damage
    fifth_event = history.pop(0)
    self.assertTrue(isinstance(fifth_event, events.LightWoundsDamageEvent))
    self.assertEqual(self.shiba, fifth_event.subject)
    self.assertEqual(self.attacker, fifth_event.target)
    self.assertEqual(10, fifth_event.damage)

  def test_damage_parry_succeeded(self):
    # set up engine
    engine = CombatEngine(self.context)
    # rig shiba's rolls
    roll_provider = TestRollProvider()
    roll_provider.put_skill_roll('parry', 51)
    roll_provider.put_damage_roll(10)
    self.shiba.set_roll_provider(roll_provider)
    # play parry action
    engine.event(self.take_action_event)
    # assert expected parry action state
    self.assertEqual(51, self.parry.skill_roll())
    self.assertTrue(self.parry.is_success())
    # assert expected attack action state
    self.assertFalse(self.attack.is_hit())
    self.assertTrue(self.attack.parried())
    self.assertTrue(self.attack.parry_attempted())
    # assert expected damage roll params
    observed_damage_params = roll_provider.pop_observed_params('damage')
    self.assertEqual((6, 1), observed_damage_params)
    # assert expected event history
    history = engine.history()
    # take_parry
    first_event = history.pop(0)
    self.assertTrue(isinstance(first_event, shiba_school.ShibaTakeParryEvent))
    # parry_declared
    second_event = history.pop(0)
    self.assertTrue(isinstance(second_event, events.ParryDeclaredEvent))
    # parry_rolled
    third_event = history.pop(0)
    self.assertTrue(isinstance(third_event, events.ParryRolledEvent))
    self.assertEqual(51, third_event.roll)
    # parry_succeeded
    fourth_event = history.pop(0)
    self.assertTrue(isinstance(fourth_event, events.ParrySucceededEvent))
    # lw_damage
    fifth_event = history.pop(0)
    self.assertTrue(isinstance(fifth_event, events.LightWoundsDamageEvent))
    self.assertEqual(self.shiba, fifth_event.subject)
    self.assertEqual(self.attacker, fifth_event.target)
    self.assertEqual(10, fifth_event.damage)

