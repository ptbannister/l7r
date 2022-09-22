#!/usr/bin/env python3

#
# features.py
# Author: Patrick Bannister (ptbannister@gmail.com)
#
# Observe and analyze features of an L7R simulation run.
#

class SummaryFeatures(object):
  '''
  Summary of many simulation runs.
  '''
  def __init__(self):
    self._control_victories = 0
    self._test_victories = 0

  def observe(self, trial_features):
    if trial_features.get_winner() == -1:
      self._control_victories += 1
    else:
      self._test_victories += 1

  def report(self):
    return self._test_victories    


class TrialFeatures(object):
  '''
  Features of a single run.
  '''
  def __init__(self):
    self.data = {}
    self.initialize()

  def clear(self):
    self.initialize()

  def get_lw(self):
    return self.data.get('lw', 0)

  def get_phases(self):
    return self.data.get('phases', 0)

  def get_rounds(self):
    return self.data.get('rounds', 0)

  def get_sw(self):
    return self.data.get('sw', 0)

  def get_winner(self):
    return self.data.get('winner', 0)

  def initialize(self):
    self.data['lw'] = 0
    self.data['phases'] = 0
    self.data['rounds'] = 0
    self.data['sw'] = 0
    self.data['winner'] = 0

  def observe_lw(self, damage):
    self.data['lw'] += damage

  def observe_phase(self):
    self.data['phases'] += 1

  def observe_round(self):
    self.data['rounds'] += 1

  def observe_sw(self, damage):
    self.data['sw'] += damage

  def observe_winner(self, result):
    '''
    observe_winner(result)

    Set the winner of this simulation.
    -1 = control group won
    0 = both sides lost
    1 = test group won
    '''
    self.data['winner'] = result

