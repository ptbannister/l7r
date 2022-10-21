#!/usr/bin/env python3

#
# void_point_manager.py
#
# Class to help characters reserve Void Points for future use.
#

from simulation.skills import EXTENDED_SKILLS


class VoidPointManager(object):
  '''
  Class to reserve Void Points for future use for a specific skill.

  The usual reason to do this is when a character keeps a large
  number of Light Wounds because they can handle a future Wound
  Check by spending Void Points. This class makes it possible to
  reserve Void Points for that future Wound Check, so the character
  won't spend them on something else like an attack roll or a
  special ability.
  '''
  def __init__(self):
    self._reservations = {}

  def cancel(self, skill):
    '''
    cancel(skill)
      skill (str): skill for which the reservation is being cancelled

    Removes any existing reservations for the indicated skill.
    '''
    if not isinstance(skill, str):
      raise ValueError('cancel skill must be str')
    if skill not in EXTENDED_SKILLS:
      raise ValueError('Invalid skill: {}'.format(skill))
    self._reservations.pop(skill)

  def clear(self):
    '''
    clear()

    Clears all reservations.
    '''
    self._reservations.clear()

  def reserve(self, skill, vp):
    '''
    reserve(skill, vp)
      skill (str): skill that the Void Points will be used for
      vp (int): number of Void Points to reserve

    Reserves void points for future use for the chosen skill.
    '''
    if not isinstance(skill, str):
      raise ValueError('reserve skill must be str')
    if skill not in EXTENDED_SKILLS:
      raise ValueError('Invalid skill: {}'.format(skill))
    if not isinstance(vp, int):
      raise ValueError('reserve vp must be int')
    prev_reservation = self.reserved(skill)
    self._reservations[skill] = prev_reservation + vp

  def reserved(self, skill):
    '''
    reserved(skill) -> int
      skill (str): skill of interest

    Returns the number of Void Points reserved for use for the given skill.
    '''
    if not isinstance(skill, str):
      raise ValueError('reserved skill must be str')
    if skill not in EXTENDED_SKILLS:
      raise ValueError('Invalid skill: {}'.format(skill))
    return self._reservations.get(skill, 0)

  def vp(self, character, skill):
    '''
    vp(character, skill) -> int
      character (Character): character of interest
      skill (str): skill of interest

    Returns the number of Void Points the character has available
    for the given skill.
    '''
    if not hasattr(character, 'vp'):
      raise ValueError('vp character requires Character')
    if not isinstance(skill, str):
      raise ValueError('reserve skill must be str')
    if skill not in EXTENDED_SKILLS:
      raise ValueError('Invalid skill: {}'.format(skill))
    available = character.vp() - sum([v for (k, v) in self._reservations.items() if k != skill])
    return max(available, 0)

