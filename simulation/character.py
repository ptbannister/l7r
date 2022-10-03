#!/usr/bin/env python3

#
# character.py
# Author: Patrick Bannister
# Class to represent a character in L7R combat simulations.
#

import math
import uuid

from simulation import actions, listeners, strategies
from simulation.knowledge import Knowledge
from simulation.log import logger
from simulation.modifiers import PARRY_OTHER_PENALTY
from simulation.roll import normalize_roll_params
from simulation.roll_provider import DEFAULT_ROLL_PROVIDER, RollProvider
from simulation.weapons import KATANA


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
    self._ap_base_skill = None
    self._ap_skills = []
    self._ap_spent = 0
    self._disadvantages = []
    self._discounts = {}
    self._extra_kept = {}
    self._extra_rolled = {}
    self._floating_bonuses = {}
    self._group = None
    self._interrupt_skills = []
    self._interrupt_costs = {}
    self._knowledge = Knowledge()
    self._modifiers = [ PARRY_OTHER_PENALTY ]
    # default listeners
    action_taken_listener = listeners.TakeActionListener()
    self._listeners = {
      'attack_declared': listeners.AttackDeclaredListener(),
      'attack_rolled': listeners.AttackRolledListener(),
      'gain_tvp': listeners.GainTemporaryVoidPointsListener(),
      'lw_damage': listeners.LightWoundsDamageListener(),
      'new_phase': listeners.NewPhaseListener(),
      'new_round': listeners.NewRoundListener(),
      'spend_ap': listeners.SpendAdventurePointsListener(),
      'spend_vp': listeners.SpendVoidPointsListener(),
      'sw_damage': listeners.SeriousWoundsDamageListener(),
      'take_attack': action_taken_listener,
      'take_parry': action_taken_listener,
      'take_sw': listeners.TakeSeriousWoundListener(),
      'wound_check_declared': listeners.WoundCheckDeclaredListener(),
      'wound_check_failed': listeners.WoundCheckFailedListener(),
      'wound_check_rolled': listeners.WoundCheckRolledListener(),
      'wound_check_succeeded': listeners.WoundCheckSucceededListener()
    }
    self._lw = 0
    self._lw_history = []
    self._roll_provider = DEFAULT_ROLL_PROVIDER
    self._skills = { 'attack': 1, 'parry': 1 }
    self._skill_rings = {
      'attack': 'fire',
      'counterattack': 'fire',
      'damage': 'fire',
      'double attack': 'fire',
      'feint': 'fire',
      'initiative': 'void',
      'lunge': 'fire',
      'parry': 'air',
      'wound check': 'water'
    }
    # default strategies
    self._strategies = {
      'action': strategies.HoldOneActionStrategy(),
      'attack': strategies.PlainAttackStrategy(),
      'light_wounds': strategies.KeepLightWoundsStrategy(),
      'parry': strategies.ReluctantParryStrategy(),
      'wound_check': strategies.WoundCheckStrategy()
    }
    self._sw = 0
    self._tvp = 0
    self._vp_spent = 0
    self._weapon = KATANA

  def actions(self):
    '''
    actions() -> list of int

    Returns the actions this character has remaining for the round.
    '''
    return self._actions

  def action_strategy(self):
    return self._strategies['action']

  def add_discount(self, item, discount):
    '''
    add_discount(item, discount)
      item (str): thing to discount
      discount (int): amount to discount the item

    Grant this character a future discount for buying something (a ring or skill).
    '''
    if item in self._discounts:
      self._discounts[item] += discount
    else:
      self._discounts[item] = discount

  def add_modifier(self, modifier):
    '''
    add_modifier(modifier)

    Add a modifier to this character.
    '''
    # TODO: register modifier listeners
    self._modifiers.add(modifier)

  def ap(self):
    '''
    ap() -> int

    Return the number of Adventure Points (Third Dan Free Raises) this character has available to spend.
    '''
    return (2 * self.skill(self.ap_base_skill())) - self._ap_spent

  def ap_base_skill(self):
    '''
    ap_base_skill() -> str

    Return the base skill used to calculate this character's
    Adventure Points (3rd Dan Free Raises), or None.
    '''
    return self._ap_base_skill

  def attack_strategy(self):
    return self._strategies['attack']

  def can_spend_ap(self, skill):
    '''
    can_spend_ap(skill) -> bool
      skill (str): name of a skill to check

    Returns whether this character can spend Adventure Points
    (Third Dan Free Raises) on the given skill.
    '''
    return skill in self._ap_skills

  def crippled(self):
    '''
    crippled() -> bool

    Return whether this Character is crippled.
    Crippled characters do not reroll tens on skill rolls.
    '''
    # TODO: does anything change this threshold?
    return self.sw() >= self.ring('earth')

  def event(self, event, context):
    if event.name in self._listeners.keys():
      logger.debug('{} handling {}'.format(self._name, event.name))
      yield from self._listeners[event.name].handle(self, event, context)
    else:
      logger.debug('{} ignoring {}'.format(self._name, event.name))

  def extra_kept(self, skill):
    return self._extra_kept.get(self.strip_suffix(skill), 0)

  def extra_rolled(self, skill):
    return self._extra_rolled.get(self.strip_suffix(skill), 0)

  def floating_bonuses(self, skill):
    '''
    floating_bonuses(skill) -> list of int
      skill (str): skill or thing on which the bonuses may be spent

    Returns the list of "floating bonuses" that may be spend on a skill or action. 
    '''
    result = []
    result.extend(self._floating_bonuses.get(skill, []))
    result.extend(self._floating_bonuses.get('any', []))
    return result

  def friends(self):
    return self.group()

  def gain_floating_bonus(self, skill, bonus):
    '''
    gain_floating_bonus(skill, bonus)
      skill (str): skill or thing that may receive the bonus
      bonus (int): amount of the bonus

    Gain a "floating bonus" that may be applied to the given skill
    in the future.
    If the bonus may be applied to anything, its skill should be 'any'.
    If the bonus may be applied to any attack, its skill should be 'any attack'.
    '''
    stripped_skill = self.strip_suffix(skill)
    if stripped_skill in self._floating_bonuses.keys():
      self._floating_bonuses[stripped_skill] = [bonus]
    else:
      self._floating_bonuses[stripped_skill].append(bonus)

  def gain_tvp(self, n=1):
    '''
    gain_tvp(n=1)
      n (int): number of Temporary Void Points to gain

    Gain the specified number of Temporary Void Points.
    '''
    self.tvp += n

  def get_attack_action(self, target, skill, vp=0):
    if skill == 'attack':
      return actions.AttackAction(self, target, skill, vp)
    elif skill == 'counterattack':
      return actions.AttackAction(self, target, skill, vp)
    elif skill == 'double attack':
      return actions.DoubleAttackAction(self, target, vp)
    elif skill == 'feint':
      return actions.FeintAction(self, target, skill, vp)
    elif skill == 'lunge':
      return actions.LungeAction(self, target, vp)

  def get_damage_roll_params(self, target, skill, attack_extra_rolled, vp=0):
    # calculate extra rolled dice
    ring = self.ring(self.get_skill_ring('damage'))
    my_extra_rolled = self.extra_rolled('damage') + self.extra_rolled('damage_' + skill)
    rolled = ring + my_extra_rolled + attack_extra_rolled + self.weapon().rolled()
    # calculate extra kept dice
    my_extra_kept = self.extra_kept('damage') + self.extra_kept('damage_' + skill)
    kept = self.weapon().kept() + my_extra_kept
    # calculate modifier
    mod = self.modifier('damage', None) + self.modifier('damage_' + skill, None)
    return normalize_roll_params(rolled, kept, mod)

  def get_initiative_roll_params(self):
    ring = self.ring(self.get_skill_ring('initiative'))
    rolled = ring + 1 + self.extra_rolled('initiative')
    kept = ring + self.extra_kept('initiative')
    return (rolled, kept, 0)

  def get_skill_ring(self, skill):
    '''
    get_skill_ring(skill) -> str
      skill (str): skill of interest

    Returns the ring used to use the given skill.
    '''
    return self._skill_rings.get(self.strip_suffix(skill), 0)

  def get_skill_roll_params(self, target, skill, vp=0):
    '''
    get_skill_roll_params(target, skill, vp=0) -> tuple of ints
      target (Character): target of the skill
      skill (str): skill name being used
      vp (int): number of Void Points to spend on this roll

    Returns the parameters for this chracter's skill roll using the
    specified ring and skill as a tuple of three ints
    (rolled, kept, modifier).
    '''
    ring = self.ring(self.get_skill_ring(skill))
    rolled = ring + self.skill(skill) + self.extra_rolled(skill) + vp
    kept = ring + self.extra_kept(skill) + vp
    modifier = self.modifier(target, skill)
    return normalize_roll_params(rolled, kept, modifier)

  def get_wound_check_roll_params(self, vp=0):
    '''
    get_wound_check_roll_params(vp=0) -> tuple of ints
      vp (int): number of Void Points to spend on this roll

    Returns the parameters for this chracter's wound check roll
    as a tuple of three ints (rolled, kept, modifier).
    '''
    ring = self.ring(self.get_skill_ring('wound check'))
    rolled = ring + 1 + self.extra_rolled('wound check') + vp
    kept = ring + self.extra_kept('wound check')
    modifier = self.modifier(None, 'wound check')
    return normalize_roll_params(rolled, kept, modifier)

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
    priority += self.ring('void')
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

  def max_ap_per_roll(self):
    '''
    max_ap_per_roll() -> int

    Return the maximum number of Adventure Points (3rd Dan Free Raises)
    this character may spend on a single roll.
    '''
    if self.ap_base_skill() is not None:
      return self.skill(self.ap_base_skill())
    else:
      return 0

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
    return (self.ring('earth') * 2) + bonus

  def max_vp(self):
    '''
    max_vp() -> int

    Return this character's capacity for Void Points, not including Temporary Void Points.
    '''
    return min([self.ring(ring) for ring in RING_NAMES]) + self.skill('worldliness')

  def max_vp_per_roll(self):
    '''
    max_vp_per_roll() -> int

    Return the maximum number of VP this character may spend on a single roll.
    '''
    return min([self.ring(ring) for ring in RING_NAMES])

  def modifier(self, target, skill):
    '''
    modifier(target, skill) -> int

    Returns the modifier (positive or negative) for using the given skill on a target.
    '''
    return sum([mod.apply(self, target, skill) for mod in self._modifiers])

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

  def ring(self, ring):
    '''
    ring(ring) -> int
      ring (str):  name of ring of interest

    Return this character's rank in the named ring.
    '''
    return self._rings[ring]

  def roll_damage(self, target, skill, attack_extra_rolled=0, vp=0):
    '''
    roll_damage(target, skill, attack_extra_rolled, vp=0) -> int
      target (Character): target of the damage roll
      skill (str): name of the skill used for the attack
      attack_extra_rolled (int): number of extra rolled dice from the attack roll
      vp (int): number of Void Points to spend on the roll

    Roll damage for this Character against the specified target,
    using the specified skill, with the given number of extra rolled
    dice because of the attack, with the given number of VP.

    This is the function that should be used by other classes to
    make a Character roll damage.
    '''
    rolled, kept, mod = self.get_damage_roll_params(target, skill, attack_extra_rolled, vp)
    roll = self.roll_provider().get_damage_roll(rolled, kept) + mod
    logger.debug('{} rolled damage: {}'.format(self._name, roll))
    return roll

  def roll_initiative(self):
    '''
    roll_initiative() -> list of ints

    Roll Initiative for this character.

    This is the function that should be used by other classes to
    make a Character roll initiative.
    '''
    (rolled, kept, mod) = self.get_initiative_roll_params()
    self._actions = self.roll_provider().get_initiative_roll(rolled, kept)
    logger.debug('{} rolled initiative: {}'.format(self._name, self._actions))
    return self._actions

  def roll_provider(self):
    return self._roll_provider

  def roll_skill(self, target, skill, vp=0):
    '''
    roll_skill(skill, vp=0) -> int
      target (Character): character targeted with the skill
      skill (str): skill used for this roll
      vp (int): number of Void Points to spend on the roll

    Roll a skill for this character against the specified target.
    '''
    (rolled, kept, mod) = self.get_skill_roll_params(target, skill, vp)
    explode = not self.crippled()
    roll = self.roll_provider().get_skill_roll(self.strip_suffix(skill), rolled, kept, explode) + mod
    logger.debug('{} rolled {}: {}'.format(self._name, skill, roll))
    return roll

  def roll_wound_check(self, damage, vp=0):
    '''
    roll_wound_check(damage, vp=0, ap=0) -> int
      damage (int): light wound total for the wound check
      vp (int): number of Void Points to spend on the roll

    Roll a Wound Check for this character.
    '''
    (rolled, kept, mod) = self.get_wound_check_roll_params(vp)
    roll = self.roll_provider().get_wound_check_roll(rolled, kept) + mod
    logger.debug('{} rolled wound check: {}'.format(self._name, roll))
    return roll

  def set_action_strategy(self, strategy):
    self._strategies['action'] = strategy

  def set_attack_strategy(self, strategy):
    self._strategies['attack'] = strategy

  def set_extra_rolled(self, skill, extra_rolled=1):
    '''
    set_extra_rolled(skill, extra_rolled)
      skill (str): skill name
      extra_rolled (int): number of extra rolled dice.

    Set extra rolled dice for the given skill.
    '''
    self._extra_rolled[skill] = extra_rolled

  def set_extra_kept(self, skill, extra_kept):
    '''
    set_extra_kept(skill, extra_rolled)
      skill (str): skill name
      extra_kept (int): number of extra kept dice.

    Set extra kept dice for the given skill.
    '''
    self._extra_kept[skill] = extra_rolled

  def set_group(self, group):
    self._group = group

  def set_interrupt_cost(self, skill, actions):
    '''
    set_interrupt_cost(skill, action)
      skill (str): skill to set
      actions (int): number of actions to interrupt

    Set the interrupt cost for this character to use an action.
    '''
    self._interrupt_costs[skill] = actions

  def set_listener(self, event_name, listener):
    '''
    set_listener(event_name, listener)
      event_name (str): name of the event to listen for
      listener (Listener): listener to handle this event

    Set this character's listener for a named event.
    '''
    self._listeners[event_name] = listener

  def set_parry_strategy(self, strategy):
    self._strategies['parry'] = strategy

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

  def set_roll_provider(self, roll_provider):
    '''
    set_roll_provider(roll_provider)
      roll_provider (RollProvider): a RollProvider capable of doing
        rolls for damage, initiative, skills, and wound checks.

    Set an alternate roll provider for this character.
    Intended for use in testing to rig rolls for predictable outcomes.
    '''
    # verify the given roll_provider satisfies the roll provider API
    if not isinstance(roll_provider, RollProvider):
      raise ValueError('roll_provider must be a RollProvider')
    self._roll_provider = roll_provider

  def set_skill(self, skill, rank):
    '''
    set_skill(skill, rank)
      skill (str): name of skill to set
      rank (int): new skill rank

    Set this character's skill at a new rank.
    '''
    self._skills[skill.lower()] = rank

  def set_strategy(self, name, strategy):
    self._strategies[name] = strategy

  def skill(self, skill):
    '''
    skill(skill) -> int
      skill (str): name of skill of interest

    Returns this character's rank in the given skill.

    Skills may contain an underscore character and a suffix,
    such as 'parry_other'. In this case, the underscore and suffix
    are stripped before the lookup.
    '''
    return self._skills.get(self.strip_suffix(skill), 0)

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

  def spend_floating_bonus(self, skill, bonus):
    '''
    spend_floating_bonus(skill, bonus)
      skill (str): skill or thing the bonus was used for
      bonus (int): amount of bonus being spent
    
    Spend a floating bonus for the given skill.
    '''
    self._floating_bonuses[skill].remove(bonus)

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

  def strip_suffix(self, word):
    if word is not None and word.find('_') > 0:
      return word[:word.find('_')]
    else:
      return word

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

  def tn_to_hit(self):
    return 5 * (1 + self.skill('parry'))

  def tvp(self):
    '''
    tvp() -> int

    Return the number of Temporary Void Points this character has available to spend.
    Characters should spend TVP very freely.
    '''
    return self._tvp

  def vp(self):
    '''
    vp() -> int

    Return the number of Void Points this character has available to spend.
    '''
    return self.max_vp() - self._vp_spent + self._tvp

  def weapon(self):
    return self._weapon

  def wound_check(self, roll, lw=None):
    '''
    wound_check(roll, lw=None) -> int
      wound_check_roll (int): wound check roll
      lw (int): light wounds taken. Defaults to character's current lw total.

    Returns the number of Serious Wounds that would be taken
    from a wound check roll against a damage amount.

    This function is only a Serious Wound calculator. It does not
    cause the character to take Serious Wounds when used. To
    inflict Serious Wounds, use the take_sw function.
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

