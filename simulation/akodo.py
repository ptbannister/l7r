#!/usr/bin/env python3

#
# akodo.py
# Author: Patrick Bannister (ptbanni@gmail.com)
# Implement Akodo Bushi School.
#

from simulation.listeners import Listener
from simulation.modifiers import FreeRaise
from simulation.schools import BaseSchool
from simulation.strategies import Strategy


class AkodoBushiSchool(BaseSchool):
  def __init__(self, skills_dict):
    super().__init__(skills_dict)
  
  def ap_base_skill(self):
    return None

  def apply_rank_five_ability(self, character):
    character.set_listener('lw_damage', AkodoLightWoundsDamageListener())

  def apply_rank_four_ability(self, character):
    self.apply_school_ring_raise_and_discount(character)
    character.set_listener('wound_check_declared', AkodoWoundCheckDeclaredListener())

  def apply_rank_three_ability(self, character):
    character.set_listener('wound_check_succeeded', AkodoWoundCheckSucceededListener())

  def apply_special(self, character):
    character.set_listener('attack_failed', AkodoAttackFailedListener())
    character.set_listener('attack_succeeded', AkodoAttackSucceededListener())

  def extra_rolled(self):
    return ['double attack', 'feint', 'wound check']

  def free_raises(self):
    return { FreeRaise('wound check') }

  def name(self):
    return 'Akodo Bushi School'

  def school_knacks(self):
    return ['double attack', 'feint', 'iaijutsu']

  def school_ring(self):
    return 'water'


class AkodoAttackFailedListener(Listener):
  '''
  Listener to implement the Akodo special ability
  to gain 1 TVP on a failed feint.
  '''
  def handle(self, character, event, context):
    if isinstance(event, AttackFailedEvent):
      if event.subject() == character:
        if event.skill() == 'feint':
          yield GainTemporaryVoidPointEvent(character, 1)

class AkodoAttackSucceededListener(Listener):
  '''
  Listener to implement the Akodo special ability
  to gain 4 TVP on a successful feint.
  '''
  def handle(self, character, event, context):
    if isinstance(event, AttackSucceededEvent):
      if event.subject() == character:
        if event.skill() == 'feint':
          yield GainTemporaryVoidPointEvent(character, 4)

class AkodoLightWoundsDamageListener(Listener):
  '''
  Listener to implement the Akodo 5th Dan technique.
  '''
  def __init__(self):
    self._strategy = AkodoFifthDanStrategy(Strategy)

  def handle(self, character, event, context):
    if isinstance(event, LightWoundsDamageEvent):
      if event.target == character:
        character.take_lw(event.damage)
        character.knowledge().observe_damage_roll(event.target, event.damage)
        yield from character.wound_check_strategy().recommend(character, event, context)
        yield from self._strategy.recommend(character, event, context)

class AkodoFifthDanStrategy(Strategy):
  '''
  Strategy to decide how to use the Akodo 5th Dan technique
  to spend VP after taking damage to directly inflict 10 LW
  per VP spent to the attacker.
  '''
  def recommend(self, character, event, context):
    if isinstance(event, LightWoundsDamageEvent):
      if event.target == character:
        # calculate max vp spendable on damage
        max_vp = min(character.vp(), character.max_vp_per_roll())
        # TODO: implement a little more intelligence
        yield SpendVoidPointsEvent(character, max_vp)
        yield LightWoundsDamageEvent(character, event.target, 10 * max_vp)


class AkodoWoundCheckSucceededListener(Listener):
  '''
  Listener to implement the Akodo 3rd Dan technique
  to gain a floating bonus after a successful Wound Check.
  '''
  def handle(self, character, event, context):
    if isinstance(event, WoundCheckSucceededEvent):
      if event.subject == character:
        bonus = ((event.roll - event.damage) // 5) * character.skill('attack')
        character.gain_floating_bonus('attack_any', bonus)
        # if the character may keep LW, consult the character's light wounds strategy
        yield from character.light_wounds_strategy().recommend(character, event, context)


class AkodoWoundCheckDeclaredListener(Listener):
  '''
  Listener to implement the Akodo 4th Dan technique
  to spend Void Points after a Wound Check roll to
  apply Free Raises to the roll.
  '''
  def __init__(self):
    self._strategy = AkodoWoundCheckRolledStrategy()

  def handle(self, character, event, context):
    if isinstance(event, WoundCheckDeclaredEvent):
      if event.subject == character:
        roll = character.roll_wound_check(event.damage, event.vp)
        event = WoundCheckRolledEvent(character, event.damage, roll)
        yield from self._strategy.recommend(character, event, context)


class AkodoWoundCheckRolledStrategy(Strategy):
  '''
  Strategy for the Akodo 4th Dan technique to decide
  whether to spend VP to improve a wound check roll.
  '''
  def recommend(self, character, event, context):
    if isinstance(event, WoundCheckRolledEvent):
      if event.target == character:
        # how many wounds would I take?
        expected_sw = character.wound_check(event.roll)
        if expected_sw == 0:
          # ignore it if no SW expected
          yield event
        else:
          # spend VP to reduce SW
          max_spend = min(character.vp(), character.max_vp_per_roll())
          prev_expected_sw = expected_sw
          chosen_spend = 0
          for vp in range(1, max_spend):
            new_roll = event.roll + (5 * vp)
            expected_sw = character.wound_check(new_roll)
            if expected_sw < prev_expected_sw:
              chosen_spend = vp
            prev_expected_sw = expected_sw
          # send a WoundCheckRolledEvent with the adjusted roll
          # wrap in a ResourcesSpentEvent so a Listener can spend character resources
          new_roll = event.roll + (5 * chosen_spend)
          new_event = WoundCheckRolledEvent(character, event.damage, new_roll)
          if (chosen_spend > 0):
            yield VoidPointsSpentEvent(chosen_spend)
          yield WoundCheckRolledEvent(character, event.damage, new_roll)

