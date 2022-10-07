#!/usr/bin/env python3

#
# skills.py
#
# Defines skills that a character may buy in the L7R combat simulator.
#
# The word "skill" is slightly overloaded in this package. In classes
# and functions it sometimes refers to things that are not
# purchasable skills, such as "wound check" and "damage".
#
# In this module, skills refers to skills that a character may buy
# and use with the roll_skill function.
#

ADVANCED_SKILLS = [
  'acting',
  'attack',
  'commerce',
  'counterattack',
  'double attack',
  'feint',
  'history',
  'iaijutsu',
  'interrogation',
  'manipulation',
  'parry',
  'underworld'
]

BASIC_SKILLS = [
  'bragging',
  'culture',
  'etiquette',
  'heraldry',
  'intimidation',
  'investigation',
  'law',
  'precepts',
  'sincerity',
  'sneaking',
  'strategy',
  'tact'
]

ADVANCED_SKILL_COST = {
  1: 4,
  2: 4,
  3: 6,
  4: 8,
  5: 10
}

BASIC_SKILL_COST = {
  1: 2,
  2: 2,
  3: 3,
  4: 3,
  5: 3
}


class Skill(object):
  def __init__(self, name):
    self._name = name

  def is_advanced(self):
    raise NotImplementedError()

  def cost(self, rank, original_rank=0):
    raise NotImplementedError()

  def is_advanced(self):
    raise NotImplementedError()

  def get(self):
    if self.name() in ADVANCED_SKILLS:
      return AdvancedSkill(self.name())
    elif self.name() in BASIC_SKILLS:
      return BasicSkill(self.name())
    else:
      raise ValueError('{} is not a valid skill'.format(self.name()))

  def name(self):
    return self._name


class AdvancedSkill(Skill):
  def __init__(self, name):
    if name not in ADVANCED_SKILLS:
      raise ValueError('{} is not a valid advanced skill'.format(name))
    self._name = name

  def cost(self, rank, original_rank=0):
    if rank > 5:
      raise ValueError('May not raise a skill beyond rank 5')
    return sum([ADVANCED_SKILL_COST[i] for i in range(original_rank + 1, rank + 1)])

  def is_advanced(self):
    return True


class BasicSkill(Skill):
  def __init__(self, name):
    if name not in BASIC_SKILLS:
      raise ValueError('{} is not a valid basic skill'.format(name))
    self._name = name

  def cost(self, rank, original_rank=0):
    if rank > 5:
      raise ValueError('May not raise a skill beyond rank 5')
    return sum([BASIC_SKILL_COST[i] for i in range(original_rank + 1, rank + 1)])

  def is_advanced(self):
    return False

