#!/usr/bin/env python3

#
# bayushi_school.py
# Author: Patrick Bannister (ptbanni@gmail.com)
# Implement Bayushi Bushi School.
#

from simulation.actions import FeintAction
from simulation.character import Character
from simulation.listeners import Listener
from simulation.log import logger
from simulation.modifiers import FreeRaise
from simulation.roll_params import DefaultRollParameterProvider, RollParameterProvider, normalize_roll_params
from simulation.schools import BaseSchool
from simulation.strategies import BaseAttackStrategy, Strategy, UniversalAttackStrategy


class BayushiBushiSchool(BaseSchool):
  def __init__(self, skills_dict):
    super().__init__(skills_dict)
  
  def ap_base_skill(self):
    return None

  def apply_rank_five_ability(self, character):
    character.wound_check = bayushi_wound_check

  def apply_rank_four_ability(self, character):
    self.apply_school_ring_raise_and_discount(character)
    character.set_listener('attack_failed', BayushiAttackFailedListener())
    character.set_listener('attack_succeeded', BayushiAttackSucceededListener())

  def apply_rank_three_ability(self, character):
    character.set_strategy('attack', BAYUSHI_ATTACK_STRATEGY)

  def apply_special(self, character):
    character.set_roll_parameter_provider(BAYUSHI_ROLL_PARAMETER_PROVIDER)

  def extra_rolled(self):
    return ['double attack', 'iaijutsu', 'wound check']

  def free_raises(self):
    return { FreeRaise('double attack') }

  def name(self):
    return 'Bayushi Bushi School'

  def school_knacks(self):
    return ['double attack', 'feint', 'iaijutsu']

  def school_ring(self):
    return 'fire'


class BayushiAttackStrategy(UniversalAttackStrategy):
  def get_attack_action(self, subject, target, skill, vp=0):
    if skill == 'feint':
      return BayushiFeintAction(subject, target, vp)
    else:
      return super().get_attack_action(subject, target, skill, vp)

BAYUSHI_ATTACK_STRATEGY = BayushiAttackStrategy()


class BayushiRollParameterProvider(DefaultRollParameterProvider):
  '''
  Custom RollParameterProvider to implement the Bayushi special ability
  to apply Void Points spent on attack rolls to damage rolls.
  '''
  def get_damage_roll_params(self, character, target, skill, attack_extra_rolled, vp=0):
    # calculate extra rolled dice
    ring = character.ring(character.get_skill_ring('damage'))
    my_extra_rolled = character.extra_rolled('damage') + character.extra_rolled('damage_' + skill)
    rolled = ring + my_extra_rolled + attack_extra_rolled + character.weapon().rolled() + vp
    # calculate extra kept dice
    my_extra_kept = character.extra_kept('damage') + character.extra_kept('damage_' + skill)
    kept = character.weapon().kept() + my_extra_kept + vp
    # calculate modifier
    mod = character.modifier('damage', None) + character.modifier('damage_' + skill, None)
    return normalize_roll_params(rolled, kept, mod)

BAYUSHI_ROLL_PARAMETER_PROVIDER = BayushiRollParameterProvider()


def bayushi_wound_check(character, roll, lw=None):
  '''
  get_bayushi_wound_check(character, roll, lw=None) -> int

  Returns the number of Serious Wounds that would be taken
  from a wound check roll against a damage amount.

  Implements the Bayushi 5th Dan ability to take Serious Wounds
  as if the character had half as many light wounds.
  '''
  lw = lw // 2 if lw is not None else character.lw() // 2
  return character.__class__.wound_check(character, roll, lw)


class BayushiFeintAction(FeintAction):
  def roll_damage(self):
    rolled = self.subject().skill('attack') + self.vp()
    kept = 1 + self.vp()
    modifier = self.subject().modifier(self.target(), self.skill())
    self._damage_roll = self.subject().roll_provider().get_damage_roll(rolled, kept) + modifier
    return self._damage_roll


class BayushiAttackFailedListener(Listener):
  '''
  Listener to implement the Bayushi 4th Dan ability
  to gain a floating bonus to any attack after a Feint.
  '''
  def handle(self, character, event, context):
    if isinstance(event, AttackFailedEvent):
      if event.subject() == character:
        if event.skill() == 'feint':
          character.gain_floating_bonus('attack_any', 5)


class BayushiAttackSucceededListener(Listener):
  '''
  Listener to implement the Bayushi 4th Dan ability
  to gain a floating bonus to any attack after a Feint.
  '''
  def handle(self, character, event, context):
    if isinstance(event, AttackSucceededEvent):
      if event.subject() == character:
        if event.skill() == 'feint':
          character.gain_floating_bonus('attack_any', 5)

