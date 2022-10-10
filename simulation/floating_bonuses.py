#!/usr/bin/env python3

#
# floating_bonuses.py
# Author: Patrick Bannister (ptbannister@gmail.com)
#
# A "floating bonus" is a bonus that a character may spend after
# making a roll to improve the roll.
#
# They are usually specific to a certain skill or group of skills.
#
# Unlike modifiers, they are a resource that a character uses at
# their discretion.
#

from simulation.skills import ATTACK_SKILLS


class FloatingBonus(object):
  def __init__(self, skills, bonus):
    if isinstance(skills, str):
      self._skills = [skills]
    elif isinstance(skills, list):
      for skill in skills:
        if not isinstance(skill, str):
          raise ValueError('FloatingBonus skills must be str or list of str')
      self._skills = skills 
    else:
      raise ValueError('FloatingBonus skills must be str or list of str')
    self._bonus = bonus

  def bonus(self):
    return self._bonus

  def is_applicable(self, skill):
    return skill in self._skills


class AnyAttackFloatingBonus(FloatingBonus):
  '''
  A floating bonus that may be applied to any attack.

  Used by the Akodo and Bayushi schools.
  '''
  def __init__(self, bonus):
    super().__init__(ATTACK_SKILLS, bonus)
