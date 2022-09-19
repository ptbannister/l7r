#!/usr/bin/env python3

#
# character.py
# Author: Patrick Bannister
# Class to represent a character in L7R combat simulations.
#

import math
import uuid

from simulation.listener import LightWoundsDamageListener, NewPhaseListener, NewRoundListener, SeriousWoundsDamageListener, TakeSeriousWoundListener, WoundCheckDeclaredListener, WoundCheckFailedListener, WoundCheckRolledListener, WoundCheckSucceededListener
from simulation.log import logger
from simulation.roll import InitiativeRoll, Roll
from simulation.strategy import AlwaysAttackActionStrategy, AttackStrategy, KeepLightWoundsStrategy, WoundCheckStrategy

class Character(object):

  def __init__(self, name=uuid.uuid4().hex):
    self._name = name
    self._rings = {
      'air': 2,
      'earth': 2,
      'fire': 2,
      'void': 2,
      'water': 2 }
    self._actions = []
    self._advantages = []
    self._bonuses = {}
    self._disadvantages = []
    self._listeners = {
      'lw_damage': LightWoundsDamageListener(),
      'new_phase': NewPhaseListener(),
      'new_round': NewRoundListener(),
      'sw_damage': SeriousWoundsDamageListener(),
      'take_sw': TakeSeriousWoundListener(),
      'wound_check_declared': WoundCheckDeclaredListener(),
      'wound_check_failed': WoundCheckFailedListener(),
      'wound_check_rolled': WoundCheckRolledListener(),
      'wound_check_succeeded': WoundCheckSucceededListener()
    }
    self._extra_rolled = {}
    self._lw = 0
    self._skills = { 'attack': 1, 'parry': 1 }
    self._strategies = {
      'action': AlwaysAttackActionStrategy(),
      'attack': AttackStrategy(),
      'light_wounds': KeepLightWoundsStrategy(),
      'wound_check': WoundCheckStrategy()
    }
    self._sw = 0
    self._vp_spent = 0
    # default roll provider
    self._roll_provider = self

  def actions(self):
    return self._actions

  def action_strategy(self):
    return self._strategies['action']

  def attack_strategy(self):
    return self._strategies['attack']

  def base_to_hit_tn(self):
    return 5 * (1 + self._skills.get('parry', 1))

  def event(self, event, context):
    if event.name in self._listeners.keys():
      logger.debug('{} handling {}'.format(self._name, event.name))
      return self._listeners[event.name].handle(self, event, context)
    else:
      logger.debug('{} ignoring {}'.format(self._name, event.name))
      return None

  def has_action(self):
    return len(self.actions()) > 0

  def initiative_priority(self, max_actions):
    '''
    initiative_priority(max_actions) -> int

    Calculate the initiative priority for this character.
    '''
    priority = 0
    exponent = max_actions + 1
    # initiative priority rewards lower actions
    for action in self._actions:
      priority += (10 - action) * math.pow(10, exponent)
      exponent -= 1
    # break ties with void ring
    priority += self._rings['void']
    return priority

  def is_alive(self):
    return self.sw() <= self.max_sw()

  def is_conscious(self):
    return self.sw() < self.max_sw()

  def is_fighting(self):
    # TODO: implement a surrender strategy
    return self.is_conscious()

  def get_damage_roll(self, skill, attack_extra_rolled, weapon_rolled, weapon_kept, vp=0):
    rolled = self._rings['fire'] + attack_extra_rolled + weapon_rolled + vp
    kept = weapon_kept + vp
    bonus = self._bonuses.get('damage', 0) + self._bonuses.get(skill + '_damage', 0)
    return Roll(rolled, kept).roll() + bonus

  def get_initiative_roll(self):
    rolled = self._rings['void'] + 1 + self._extra_rolled.get('initiative', 0)
    kept = self._rings['void']
    return InitiativeRoll(rolled, kept).roll()

  def get_skill_roll(self, ring, skill, vp=0):
    rolled = self._skills.get(skill, 0) + self._extra_rolled.get(skill, 0) + self._rings[ring] + vp
    kept = self._rings[ring] + vp
    bonus = self._bonuses.get(skill, 0)
    return Roll(rolled, kept).roll() + bonus

  def get_wound_check_roll(self, damage, vp=0):
    rolled = self._rings['water'] + 1 + self._extra_rolled.get('wound_check', 0)
    kept = self._rings['water']
    bonus = self._bonuses.get('wound_check', 0)
    return Roll(rolled, kept).roll() + bonus

  def light_wounds_strategy(self):
    '''
    light_wounds_strategy(self) -> LightWoundsDamageStrategy
    Return the LightWoundsDamageStrategy that recommends whether this character should keep light wounds or take a serious wound.
    '''
    return self._strategies['light_wounds']

  def lw(self):
    return self._lw

  def max_sw(self):
    if 'strength of the earth' in self._advantages:
      bonus = 1
    elif 'permanent wound' in self._disadvantages:
      bonus = -1
    else:
      bonus = 0
    return (self._rings['earth'] * 2) + bonus

  def reset_lw(self):
    self._lw = 0

  def roll_damage(self, skill, attack_extra_rolled, weapon_rolled, weapon_kept, vp=0):
    roll = self._roll_provider.get_damage_roll(skill, attack_extra_rolled, weapon_rolled, weapon_kept, vp)
    logger.debug('{} rolled damage: {}'.format(self._name, roll))
    return roll

  def roll_initiative(self):
    self._actions = self._roll_provider.get_initiative_roll()
    logger.debug('{} rolled initiative: {}'.format(self._name, self._actions))
    return self._actions

  def roll_skill(self, ring, skill, vp=0):
    roll = self._roll_provider.get_skill_roll(ring, skill, vp)
    logger.debug('{} rolled {}: {}'.format(self._name, skill, roll))
    return roll

  def roll_wound_check(self, damage, vp=0):
    roll = self._roll_provider.get_wound_check_roll(damage, vp)
    logger.debug('{} rolled wound check: {}'.format(self._name, roll))
    return roll

  def set_ring(self, ring, rank):
    self._rings[ring.lower()] = rank

  def set_skill(self, skill, rank):
    self._skills[skill.lower()] = rank

  def set_roll_provider(self, roll_provider):
    '''
    set_roll_provider(roll_provider)
    Set an alternate roll provider for this character.
    Intended for use in testing to rig rolls for predictable outcomes.
    '''
    self._roll_provider = roll_provider

  def set_strategy(self, name, strategy):
    self._strategies[name] = strategy

  def sw(self):
    return self._sw

  def take_lw(self, amount):
    logger.debug('{} takes {} Light Wounds'.format(self._name, amount))
    self._lw += amount

  def take_sw(self, amount):
    logger.debug('{} takes {} Serious Wounds'.format(self._name, amount))
    self._sw += amount

  def wound_check(self, roll, lw=None):
    '''
    wound_check(roll, lw=None) -> int
      wound_check_roll (int): wound check roll
      lw (int): light wounds taken. Defaults to character's current lw total.

    Returns the number of Serious Wounds that would be taken
    from a wound check roll against a damage amount.
    '''
    if lw is None:
      lw = self.lw()
    if roll <= lw:
      return 1 + ((lw - roll) // 10)
    else:
      return 0

  def wound_check_strategy(self):
    '''
    wound_check_strategy() -> WoundCheckStrategy
    Return a WoundCheckStrategy that recommends how this character will spend VP on wound checks.
    '''
    return self._strategies['wound_check']

