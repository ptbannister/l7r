#!/usr/bin/env python3

#
# roll_provider.py
# Author: Patrick Bannister
# Alternate roll providers for L7R combat simulations.
#

class TestRollProvider(object):
  '''
  TestRollProvider
  Class to provide predictable rolls for use in testing.
  '''

  def __init__(self):
    self._queues = {
      'damage': [],
      'initiative': [],
      'wound_check': []
    }

  def get_damage_roll(self, skill, attack_extra_rolled, weapon_rolled, weapon_kept, vp=0):
    if len(self._queues['damage']) == 0:
      raise IndexError('No roll queued for damage')
    return self._queues['damage'].pop(0)

  def get_initiative_roll(self):
    if len(self._queues['initiative']) == 0:
      raise IndexError('No roll queued for initiative')
    return self._queues['initiative'].pop(0)

  def get_skill_roll(self, ring, skill, ap=0, vp=0):
    if skill not in self._queues.keys():
      raise KeyError('No roll queued for ' + skill)
    elif len(self._queues[skill]) == 0:
      raise IndexError('No roll queued for ' + skill)
    return self._queues[skill].pop(0)

  def get_wound_check_roll(self, damage, ap=0, vp=0):
    if len(self._queues['wound_check']) == 0:
      raise IndexError('No roll queued for wound_check')
    return self._queues['wound_check'].pop(0)

  def put_damage_roll(self, result):
    self._queues['damage'].append(result)

  def put_initiative_roll(self, result):
    if isinstance(result, list):
      self._queues['initiative'].append(result)
    else:
      raise ValueError('Initiative rolls should be sequences of ints')

  def put_wound_check_roll(self, result):
    self._queues['wound_check'].append(result)

  def put_skill_roll(self, skill, result):
    if skill in self._queues.keys():
      self._queues[skill].append(result)
    else:
      self._queues[skill] = [result]

  def put_wound_check_roll(self, result):
    self._queues['wound_check'].append(result)

