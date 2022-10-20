#!/usr/bin/env python3

#
# professions.py
# Author: Patrick Bannister (ptbannister@gmail.com)
# Professions and profession abilities for the L7R combat simulator
#

from abc import ABC, abstractmethod

from simulation.action_factory import DefaultActionFactory
from simulation.actions import AttackAction
from simulation.roll import BaseRoll
from simulation.roll_params import DefaultRollParameterProvider, normalize_roll_params
from simulation.roll_provider import DefaultRollProvider


# list of supported ability names
ABILITY_NAMES = [
  'missed_attack_bonus',
  'parry_penalty',
  'weapon_damage_bonus',
  'rolled_damage_bonus',
  'crippled_bonus',
  'initiative_bonus',
  'wound_check_bonus',
  'damage_penalty',
  'failed_parry_damage_bonus',
  'wound_check_penalty'
]


class Profession(object):
  '''
  Class to represent a character's chosen abilities in a peasant
  profession.
  '''
  def __init__(self):
    self._abilityd = {}

  def ability(self, name):
    '''
    ability(name) -> int
      name (str): the name of the ability of interest

    Returns the number of times a character has taken the named
    ability (0, 1, or 2)
    '''
    if not isinstance(name, str):
      raise ValueError('ability requires a str')
    if name not in ABILITY_NAMES:
      raise ValueError('{} is not a valid profession ability'.format(name))
    return self._abilityd.get(name, 0)

  def take_ability(self, name):
    '''
    take_ability(name)
      name (str): the name of the ability to take

    Take the named ability. Abilities may be taken at most twice.
    '''
    if not isinstance(name, str):
      raise ValueError('take_ability requires a str')
    if name not in ABILITY_NAMES:
      raise ValueError('{} is not a valid profession ability'.format(name))
    cur_rank = self.ability(name)
    if cur_rank == 2:
      raise RuntimeError('Profession ability {} may not be raised above 2'.format(name))
    self._abilityd[name] = cur_rank +  1

  def __len__(self):
    '''
    __len__() -> int

    Returns the number of abilities taken.
    Multiple levels of an ability count as two abilities taken.
    '''
    return sum(self._abilityd.values())


class ProfessionAbility(ABC):
  '''
  Class to represent a peasant profession ability. Its apply method
  should modify the given character object to add the ability to
  the character.
  '''
  @abstractmethod
  def apply(self, character, profession):
    '''
    apply(character, profession)
      character (Character): character who took the ability
      profession (Profession): the character's Profession object

    Updates the character to confer this profession ability.
    '''
    pass


def get_profession_ability(name):
  '''
  get_profession_ability(name) -> ProfessionAbility
    name (str): name of the desired ability

  Returns a ProfessionAbility instance capable of applying the
  named ability to a character.
  '''
  if not isinstance(name, str):
    raise ValueError('get_profession_ability requires str')
  if name == 'crippled_bonus':
    return CrippledBonusAbility()
  elif name == 'damage_penalty':
    return DamagePenaltyAbility()
  elif name == 'failed_parry_damage_bonus':
    return FailedParryDamageBonusAbility()
  elif name == 'initiative_bonus':
    return InitiativeBonusAbility()
  elif name == 'missed_attack_bonus':
    return MissedAttackBonusAbility()
  elif name == 'parry_penalty':
    return ParryPenaltyAbility()
  elif name == 'rolled_damage_bonus':
    return RolledDamageBonusAbility()
  elif name == 'weapon_damage_bonus':
    return RolledDamageBonusAbility()
  elif name == 'wound_check_bonus':
    return WoundCheckBonusAbility()
  elif name == 'wound_check_penalty':
    return WoundCheckPenaltyAbility()
  else:
    raise ValueError('{} is not a valid profession ability'.format(name))


class CrippledBonusAbility(ProfessionAbility):
  '''
  Represents the "crippled_bonus" Wave Man profession ability:
  "You may reroll 10s on a single die when crippled."
  '''
  def apply(self, character, profession):
    character.set_roll_provider(profession)


class DamagePenaltyAbility(ProfessionAbility):
  '''
  Represents the "damage_penalty" Wave Man profession ability:
  "When someone is keeping at least one extra die of damage from
  exceeding their attack roll TN, subtract 5 from the damage."
  '''
  def apply(self, character, profession):
    # TODO: implement this by adding an expiring Modifier to the
    # attacker after AttackSucceededEvent
    raise NotImplementedError()


class FailedParryDamageBonusAbility(ProfessionAbility):
  '''
  Represents the "failed_parry_damage_bonus" Wave Man profession
  ability:
  "When someone unsuccessfully tries to parry an attack, you may
  roll two of the extra damage dice that you would have rolled
  had they not attempted to parry."
  '''
  def apply(self, character, profession):
    character.set_action_factory(WaveManActionFactory(profession))


class InitiativeBonusAbility(ProfessionAbility):
  '''
  Represents the "initiative_bonus" Wave Man profession ability:
  "Roll one extra unkept die on initiative."
  '''
  def apply(self, character, profession):
    character.set_extra_rolled('initiative', 1)


class MissedAttackBonusAbility(ProfessionAbility):
  '''
  Represents the "missed_attack_bonus" Wave Man profession ability:
  "When you make an attack roll that would miss, raise it by 5. Any
  parry attempt against an attack that receives a free raise in this
  manner automatically succeeds."
  '''
  def apply(self, character, profession):
    # implemented in WaveManAttackAction
    character.set_action_factory(WaveManActionFactory(profession))


class ParryPenaltyAbility(ProfessionAbility):
  '''
  Represents the "parry_penalty" Wave Man profession ability:
  "Raise the TN of someone trying to parry one of your attacks by 5."
  '''
  def apply(self, character, profession):
    # implemented in WaveManAttackAction
    character.set_action_factory(WaveManActionFactory(profession))


class RolledDamageBonusAbility(ProfessionAbility):
  '''
  Represents the "rolled_damage_bonus" Wave Man profession ability:
  "Round your damage rolls up to the nearest multiple of 5. If the
  roll is already a multiple of 5, then raise it by 3."
  '''
  def apply(self, character, profession):
    # implemented in WaveManAttackAction
    character.set_action_factory(WaveManActionFactory(profession))


class WeaponDamageBonusAbility(ProfessionAbility):
  '''
  Represents the "weapon_damage_bonus" Wave Man profession ability:
  "When using a weapon that deals less than 4k2 damage, add an extra
  rolled damage die to the weapon's base damage, to a maximum of 4k2
  base damage. Also, subtract 2 from your armor damage reduction
  penalty."
  '''
  def apply(self, character, profession):
    # implemented in WaveManRollParameterProvider
    character.set_roll_parameter_provider( \
      WaveManRollParameterProvider(profession))


class WoundCheckBonusAbility(ProfessionAbility):
  '''
  Represents the "wound_check_bonus" Wave Man profession ability:
  "Roll two extra unkept dice on wound checks."
  '''
  def apply(self, character, profession):
    character.set_extra_rolled('wound check', 2)


class WoundCheckPenaltyAbility(ProfessionAbility):
  '''
  Represents the "wound_check_penalty" Wave Man profession ability:
  "Raise the TN of someone making a wound check from damage you
  dealt to them by 5. If they fail they take serious wounds as if
  the TN had not been raised."
  '''
  def apply(self, character, profession):
    # TODO: this is challenging!
    # need to somehow separate wound check TN from LW
    # might need a ResolveDamageEvent with complex internal logic
    raise NotImplementedError()


class WaveManAttackAction(AttackAction):
  '''
  AttackAction to implement the Wave Man profession abilities:

  "When you make an attack roll that would miss, raise it by 5.
  Any parry attempt against an attack that receives a free raise in
  this manner automatically succeeds."

  and:
  "Raise the TN of someone trying to parry one of your attacks by 5."

  and:
  "Round your damage rolls up to the nearest multiple of 5. If the
  roll is already a multiple of 5, then raise it by 3."

  and:
  "When someone unsuccessfully tries to parry an attack, you may
  roll two of the extra damage dice that you would have rolled
  had they not attempted to parry."
  '''
  def __init__(self, subject, target, skill='attack', vp=0):
    super().__init__(subject, target, skill, vp)
    self._used_missed_attack_bonus = False

  def ability(self, name):
    return self.subject().profession().ability(name)

  def calculate_extra_damage_dice(self, skill_roll=None, tn=None):
    if skill_roll is None:
      skill_roll = self.skill_roll()
    if tn is None:
      tn = self.tn()
    # calculate normal extra rolled damage dice
    extra_rolled = (skill_roll - self.tn()) // 5
    if self.parry_attempted():
      # failed parries usually cancel extra rolled damage dice
      # failed_parry_damage_bonus ability preserves some of
      # the extra rolled dice
      return min(extra_rolled, self.ability('failed_parry_damage_bonus') * 2)
    else:
      return extra_rolled

  def parry_tn(self):
    if self.used_missed_attack_bonus():
      # parry automatically succeeds if the missed_attack_bonus
      # ability was used
      return 0
    else:
      # apply the parry penalty ability
      penalty = self.ability('parry_penalty') * 5
      return self.skill_roll() + penalty

  def roll_attack(self):
    roll = self.subject().roll_skill(self.target(), self.skill(), self.vp())
    # apply missed_attack_bonus ability
    if roll < self.tn():
      for i in range(self.ability('missed_attack_bonus')):
        if roll < self.tn():
          roll += 5
          self.set_used_missed_attack_bonus()
    self.set_skill_roll(roll)
    return self.skill_roll()

  def roll_damage(self):
    extra_rolled = self.calculate_extra_damage_dice()
    roll = self.subject().roll_damage(self.target(), self.skill(), extra_rolled, self.vp())
    # apply damage_bonus ability
    for i in range(self.ability('rolled_damage_bonus')):
      if roll % 5 == 0:
        roll += 3
      else:
        roll += 5 - (roll % 5)
    self._damage_roll = roll
    return self._damage_roll

  def set_used_missed_attack_bonus(self):
    '''
    set_used_missed_attack_bonus()

    Sets the boolean flag to indicate that this attack used the
    missed_attack_bonus ability to hit.
    '''
    self._used_missed_attack_bonus = True

  def used_missed_attack_bonus(self):
    '''
    used_missed_attack_bonus() -> bool

    Returns whether the missed_attack_bonus ability was used
    to make this attack hit.
    '''
    return self._used_missed_attack_bonus
    

class WaveManActionFactory(DefaultActionFactory):
  '''
  ActionFactory that can return a WaveManAttackAction.
  '''
  def __init__(self, abilities):
    self._abilities = abilities

  def get_attack_action(self, subject, target, skill, vp=0):
    if skill == 'attack':
      return WaveManAttackAction(subject, target, self._abilities, skill, vp)
    else:
      return super().get_attack_action(subject, target, skill, vp)


class WaveManRoll(BaseRoll):
  '''
  Roll that implements the Wave Man profession ability
  "crippled_bonus":
  "You may reroll 10s on a single die when crippled."
  '''
  def __init__(self, rolled, kept, faces=10, explode=True, die_provider=None, always_explode=0):
    super().__init__(rolled, kept, faces, explode, die_provider)
    if not isinstance(always_explode, int):
      raise ValueError('WaveManRoll always_explode parameter must be int')
    if always_explode > 2:
      raise ValueError('WaveManRoll may not reroll more than two tens when crippled')
    self.always_explode = always_explode

  def roll(self):
    dice = [self.roll_die(faces=self.faces(), explode=self.explode()) for n in range(self._rolled)]
    if not self.explode():
      for i in range(self.always_explode):
        if 10 in dice:
          dice.remove(10)
          rerolled = 10 + self.roll_die(faces=self.faces(), explode=True)
          dice.append(rerolled)
    dice.sort(reverse=True)
    return sum(dice[:self._kept]) + self._bonus


class WaveManRollParameterProvider(DefaultRollParameterProvider):
  '''
  RollParameterProvider that implements the Wave Man profession
  ability "weapon_damage_bonus":
  "When using a weapon that deals less than 4k2 damage, add an extra
  rolled damage die to the weapon's base damage, to a maximum of 4k2
  base damage. Also, subtract 2 from your armor damage reduction
  penalty."
  '''
  def get_damage_roll_params(self, character, target, skill, attack_extra_rolled, vp=0):
    # calculate weapon dice
    weapon_rolled = character.weapon().rolled()
    ability_level = character.profession().ability('weapon_damage_bonus')
    if weapon_rolled < 4:
      weapon_rolled = min(4, weapon_rolled + ability_level)
    # calculate extra rolled dice
    ring = character.ring(character.get_skill_ring('damage'))
    my_extra_rolled = character.extra_rolled('damage')
    rolled = ring + my_extra_rolled + attack_extra_rolled + weapon_rolled
    # calculate extra kept dice
    my_extra_kept = character.extra_kept('damage') + character.extra_kept('damage_' + skill)
    kept = character.weapon().kept() + my_extra_kept
    # calculate modifier
    mod = character.modifier('damage', None) + character.modifier('damage_' + skill, None)
    return normalize_roll_params(rolled, kept, mod)


class WaveManRollProvider(DefaultRollProvider):
  '''
  RollProvider that implements the Wave Man profession ability
  "crippled_bonus" to reroll some 10s when crippled.
  '''
  def __init__(self, profession, die_provider=None):
    super().__init__(die_provider)
    if not isinstance(profession, Profession):
      raise ValueError('WaveManRollProvider __init__ requires Profession')
    self._profession = profession

  def ability(self, ability):
    return self._profession.ability(ability)

  def get_skill_roll(self, skill, rolled, kept, explode=True):
    '''
    get_skill_roll(skill, rolled, kept) -> int
      skill (str): name of skill being used
      rolled (int): number of rolled dice
      kept (int): number of kept dice
      explode (bool): whether tens should be rerolled
    
    Return a skill roll using the specified number of rolled and kept dice.
    '''
    always_explode = self.ability('crippled_bonus')
    return WaveManRoll(rolled, kept, die_provider=self.die_provider(), explode=explode, always_explode=always_explode).roll()

