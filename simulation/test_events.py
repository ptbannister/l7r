#!/usr/bin/env python3

#
# test_events.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator events module
#

import unittest

from simulation.actions import AttackAction
from simulation.character import Character
from simulation.context import EngineContext
from simulation.engine import CombatEngine
from simulation.events import AttackDeclaredEvent, AttackRolledEvent, AttackSucceededEvent, LightWoundsDamageEvent, TakeAttackActionEvent
from simulation.roll_provider import TestRollProvider


class TestTakeAttackActionEvent(unittest.TestCase):
  def test_run_hit(self):
    attacker = Character('attacker')
    target = Character('target')
    target.set_skill('parry', 5)
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
    context = EngineContext([[attacker,], [target]])
    engine = CombatEngine(context)
    # run the event
    event = TakeAttackActionEvent(attack)
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
    self.assertTrue(isinstance(first_event, TakeAttackActionEvent))
    second_event = history.pop(0)
    self.assertTrue(isinstance(second_event, AttackDeclaredEvent))
    third_event = history.pop(0)
    self.assertTrue(isinstance(third_event, AttackRolledEvent))
    self.assertEqual(31, third_event.roll)
    fourth_event = history.pop(0)
    self.assertTrue(isinstance(fourth_event, AttackSucceededEvent))
    fifth_event = engine.get_history().pop(0)
    self.assertTrue(isinstance(fifth_event, LightWoundsDamageEvent))
    self.assertEqual(target, fifth_event.target)
    self.assertEqual(15, fifth_event.amount)

