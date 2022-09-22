#!/usr/bin/env python3

#
# character.py
# Author: Patrick Bannister
# Class to represent a character in L7R combat simulations.
#

import math
import uuid

from simulation import listener, strategy
from simulation.knowledge import Knowledge
from simulation.log import logger
from simulation.roll import InitiativeRoll, Roll, normalize_roll_params


RING_NAMES = ['air', 'earth', 'fire', 'water', 'void']

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
    self._ap = 0
    self._ap_spent = 0
    self._bonuses = {}
    self._disadvantages = []
    self._extra_rolled = {}
    self._group = None
    self._interrupt_skills = []
    self._interrupt_costs = {}
    self._knowledge = Knowledge()
    action_taken_listener = listener.TakeActionListener()
    self._listeners = {
      'attack_rolled': listener.AttackRolledListener(),
      'lw_damage': listener.LightWoundsDamageListener(),
      'new_phase': listener.NewPhaseListener(),
      'new_round': listener.NewRoundListener(),
      'sw_damage': listener.SeriousWoundsDamageListener(),
      'take_attack': action_taken_listener,
      'take_parry': action_taken_listener,
      'take_sw': listener.TakeSeriousWoundListener(),
      'wound_check_declared': listener.WoundCheckDeclaredListener(),
      'wound_check_failed': listener.WoundCheckFailedListener(),
      'wound_check_rolled': listener.WoundCheckRolledListener(),
      'wound_check_succeeded': listener.WoundCheckSucceededListener()
    }
    self._lw = 0
    self._lw_history = []
    self._roll_provider = self
    self._skills = { 'attack': 1, 'parry': 1 }
    self._strategies = {
      'action': strategy.AlwaysAttackActionStrategy(),
      'attack': strategy.AttackStrategy(),
      'light_wounds': strategy.KeepLightWoundsStrategy(),
      'parry': strategy.ReluctantParryStrategy(),
      'wound_check': strategy.WoundCheckStrategy()
    }
    self._sw = 0
    self._tvp = 0
    self._vp_spent = 0

  def actions(self):
    '''
    actions() -> list of int

    Returns the actions this character has remaining for the round.
    '''
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

  def friends(self):
    return self.group()

  def group(self):
    return self._group

  def has_action(self, context):
    '''
    has_action(context) -> bool
      context (EngineContext): context to provide timing

    Return whether this character has an available action in the current phase.
    Does not consider interrupt actions.
    '''
    if len(self.actions()) == 0:
      return False
    else:
      return min(self.actions()) <= context.phase()

  def has_interrupt_action(self, skill, context):
    '''
    has_interrupt_action(skill, context) -> bool
      skill (str): name of the skill that would be used
      context (EngineContext): context to provide timing

    Return whether this character could do an interrupt action in the current phase.
    '''
    if skill in self._interrupt_skills:
      if self._interrupt_costs.get(skill, 2) <= len(self.actions()):
        return True
    return False

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
    '''
    is_alive() -> bool

    Return whether this character is alive.
    '''
    return self.sw() <= self.max_sw()

  def is_conscious(self):
    '''
    is_conscious() -> bool

    Return whether this character is still conscious.
    '''
    return self.sw() < self.max_sw()

  def is_fighting(self):
    '''
    is_fighting() -> bool

    Return whether this character is still fighting.
    '''
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

  def get_skill_roll(self, ring, skill, ap=0, vp=0):
    (rolled, kept, bonus) = self.get_skill_roll_params(ring, skill, ap, vp)
    return Roll(rolled, kept).roll() + bonus

  def get_skill_roll_params(self, ring, skill, ap=0, vp=0):
    '''
    get_skill_roll_params(ring, skill, ap=0, vp=0) -> tuple of ints
      ap (int): number of Adventure Points to spend on this roll
      vp (int): number of Void Points to spend on this roll

    Returns the parameters for this chracter's skill roll using the
    specified ring and skill as a tuple of three ints
    (rolled, kept, bonus).
    '''
    rolled = self._rings[ring] + 1 + self._extra_rolled.get(skill, 0) + vp
    kept = self._rings[ring] + vp
    bonus = self._bonuses.get(skill, 0) + (ap * 5)
    return normalize_roll_params(rolled, kept, bonus)

  def get_wound_check_roll(self, damage, ap=0, vp=0):
    '''
    get_wound_check_roll(damage, ap=0, vp=0) -> int
      damage (int): damage for this Wound Check
      ap (int): number of Adventure Points to spend on this roll
      vp (int): number of Void Points to spend on this roll
    
    Return a Wound Check roll for this character.

    Do not use this function to do a wound check roll!
    Instead, use the wound_check_roll function.
    This function is public API for the Roll Provider interface,
    but it is not really public for the Character interface.
    '''
    (rolled, kept, bonus) = self.get_wound_check_roll_params(ap, vp)
    return Roll(rolled, kept).roll() + bonus

  def get_wound_check_roll_params(self, ap=0, vp=0):
    '''
    get_wound_check_roll_params(ap=0, vp=0) -> tuple of ints
      ap (int): number of Adventure Points to spend on this roll
      vp (int): number of Void Points to spend on this roll

    Returns the parameters for this chracter's wound check roll
    as a tuple of three ints (rolled, kept, bonus).
    '''
    rolled = self._rings['water'] + 1 + self._extra_rolled.get('wound_check', 0) + vp
    kept = self._rings['water'] + vp
    bonus = self._bonuses.get('wound_check', 0) + (ap * 5)
    return normalize_roll_params(rolled, kept, bonus)

  def is_friend(self, character):
    '''
    is_friend(character) -> bool

    Returns whether a character is a friend (in the same group).
    '''
    return character in self._group

  def knowledge(self):
    '''
    knowledge() -> Knowledge

    Returns this character's Knowledge instance.
    '''
    return self._knowledge

  def light_wounds_strategy(self):
    '''
    light_wounds_strategy(self) -> KeepLightWoundsStrategy

    Return the KeepLightWoundsStrategy that recommends whether this character should keep light wounds or take a serious wound.
    '''
    return self._strategies['light_wounds']

  def lw(self):
    '''
    lw() -> int

    Return this character's current Light Wound total.
    '''
    return self._lw

  def lw_history(self):
    '''
    lw_history() -> list of ints

    Return the amounts of damage this character has taken in the past.
    Used to predict future damage.
    '''
    return self._lw_history

  def max_sw(self):
    '''
    max_sw() -> int

    Return the number of Serious Wounds this character can take
    before unconsciousness.
    '''
    if 'strength of the earth' in self._advantages:
      bonus = 1
    elif 'permanent wound' in self._disadvantages:
      bonus = -1
    else:
      bonus = 0
    return (self._rings['earth'] * 2) + bonus

  def max_vp(self):
    '''
    max_vp() -> int

    Return the maximum number of Void Points this character may spend,
    not including Temporary Void Points.
    '''
    return min(self._rings.values()) + self._skills.get('worldliness', 0)

  def name(self):
    return self._name

  def parry_strategy(self):
    return self._strategies['parry']

  def reset(self):
    self._actions = []
    self._ap_spent = 0
    self._knowledge.clear()
    self._lw = 0
    self._lw_history.clear()
    self._sw = 0
    self._tvp = 0
    self._vp_spent = 0

  def reset_lw(self):
    '''
    reset_lw()

    Reset this character's Light Wound total to zero.
    '''
    self._lw = 0

  def roll_damage(self, skill, attack_extra_rolled, weapon_rolled, weapon_kept, vp=0):
    '''
    roll_damage(skill, attack_extra_rolled, weapon_rolled, weapon_kept, vp=0) -> int
      skill (str): name of the skill used for the attack
      attack_extra_rolled (int): number of extra rolled dice from the attack roll
      weapon_rolled (int): number of rolled dice for the weapon used
      weapon_kept (int): number of kept dice for the weapon used
      vp (int): number of Void Points to spend on the roll
    '''
    roll = self._roll_provider.get_damage_roll(skill, attack_extra_rolled, weapon_rolled, weapon_kept, vp)
    logger.debug('{} rolled damage: {}'.format(self._name, roll))
    return roll

  def roll_initiative(self):
    '''
    roll_initiative() -> list of ints

    Roll Initiative for this character.
    '''
    self._actions = self._roll_provider.get_initiative_roll()
    logger.debug('{} rolled initiative: {}'.format(self._name, self._actions))
    return self._actions

  def roll_skill(self, ring, skill, ap=0, vp=0):
    '''
    roll_skill(damage, vp=0, ap=0) -> int
      damage (int): light wound total for the wound check
      ap (int): number of Third` Dan Free Raises ("Adventure Points")
                to spend on the roll
      vp (int): number of Void Points to spend on the roll

    Roll a skill for this character.
    '''
    self.spend_ap(skill, ap)
    self.spend_vp(vp)
    roll = self._roll_provider.get_skill_roll(ring, skill, ap, vp)
    logger.debug('{} rolled {}: {}'.format(self._name, skill, roll))
    return roll

  def roll_wound_check(self, damage, ap=0, vp=0):
    '''
    roll_wound_check(damage, vp=0, ap=0) -> int
      damage (int): light wound total for the wound check
      ap (int): number of Third` Dan Free Raises ("Adventure Points")
                to spend on the roll
      vp (int): number of Void Points to spend on the roll

    Roll a Wound Check for this character.
    '''
    self.spend_ap('wound_check', ap)
    self.spend_vp(vp)
    roll = self._roll_provider.get_wound_check_roll(damage, vp)
    logger.debug('{} rolled wound check: {}'.format(self._name, roll))
    return roll

  def set_action_strategy(self, strategy):
    self._strategies['action'] = strategy

  def set_attack_strategy(self, strategy):
    self._strategies['attack'] = strategy

  def set_parry_strategy(self, strategy):
    self._strategies['parry'] = strategy

  def set_group(self, group):
    self._group = group

  def set_ring(self, ring, rank):
    '''
    set_ring(ring, rank)
      ring (str): name of ring to set
      rank (int): new ring rank

    Set this character's ring at a new rank.
    '''
    if ring not in RING_NAMES:
      raise ValueError('{} is not a ring'.format(ring))
    self._rings[ring.lower()] = rank

  def set_skill(self, skill, rank):
    '''
    set_skill(skill, rank)
      skill (str): name of skill to set
      rank (int): new skill rank

    Set this character's skill at a new rank.
    '''
    self._skills[skill.lower()] = rank

  def set_roll_provider(self, roll_provider):
    '''
    set_roll_provider(roll_provider)
      roll_provider (object): An object that fulfills the roll
      provider API.

    Set an alternate roll provider for this character.
    Intended for use in testing to rig rolls for predictable outcomes.
    '''
    # verify the given roll_provider satisfies the roll provider API
    if not hasattr(roll_provider, 'get_initiative_roll'):
      raise ValueError('Roll provider must implement get_initiative_roll')
    if not hasattr(roll_provider, 'get_skill_roll'):
      raise ValueError('Roll provider must implement get_skill_roll')
    if not hasattr(roll_provider, 'get_wound_check_roll'):
      raise ValueError('Roll provider must implement get_wound_check_roll')

    self._roll_provider = roll_provider

  def set_strategy(self, name, strategy):
    self._strategies[name] = strategy

  def spend_ap(self, skill, n):
    '''
    spend_ap(skill, n)
      skill (str): name of the skill for which points are being spent
      n (int): number of points being spent

    Spend Adventure Points (Third Dan Free Raises) if allowed.
    '''
    if n > 0:
      if self._ap - self._ap_spent < n:
        raise ValueError('Not enough Adventure Points')
      self._ap_spent += n

  def spend_vp(self, n):
    '''
    spend_vp(n)
      n (int): number of Void Points to spend

    Spend Void Points.
    '''
    if self.vp() < n:
      raise ValueError('Not enough Void Points')
    still_unspent = n
    while still_unspent > 0:
      if self._tvp > 0:
        self._tvp -= 1
        still_unspent -= 1
      elif self.vp() > 0:
        self._vp_spent += 1
        still_unspent -= 1
      else:
        raise ValueError('Not enough Void Points')

  def sw(self):
    '''
    sw() -> int

    Return the number of Serious Wounds this character has taken.
    '''
    return self._sw

  def sw_remaining(self):
    '''
    sw_remaining() -> int

    Return the number of Serious Wounds this character has remaining
    before unconsciousness.
    '''
    return self.max_sw() - self.sw() 

  def take_lw(self, amount):
    '''
    take_lw(amount)
      amount (int): amount of Light Wounds to take

    Add the given amount of Light Wounds to this character's Light
    Wound total.
    '''
    logger.debug('{} takes {} Light Wounds'.format(self._name, amount))
    self._lw += amount
    self._lw_history.append(amount)

  def take_sw(self, amount):
    logger.debug('{} takes {} Serious Wounds'.format(self._name, amount))
    self._sw += amount

  def vp(self):
    '''
    vp() -> int

    Return the number of Void Points this character has available to spend.
    '''
    return self.max_vp() - self._vp_spent + self._tvp

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

  def wound_check_params(self, vp=0):
    '''
    wound_check_params(vp=0) -> tuple of ints
      vp (int): number of Void Points to spend on this wound check roll

    Returns the tuple of (rolled, kept, bonus) for this character's wound checks.
    '''
    rolled = self._rings['water'] + 1 + self._extra_rolled.get('wound_check', 0) + vp
    kept = self._rings['water'] + vp
    bonus = self._bonuses.get('wound_check', 0)
    return (rolled, kept, bonus)

  def wound_check_strategy(self):
    '''
    wound_check_strategy() -> WoundCheckStrategy
    Return a WoundCheckStrategy that recommends how this character will spend VP on wound checks.
    '''
    return self._strategies['wound_check']

