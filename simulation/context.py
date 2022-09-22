
import os

from simulation.exceptions import CombatEnded
from simulation.features import TrialFeatures
from simulation.roll import normalize_roll_params

script_path = os.path.realpath(__file__)
script_dirpath = os.path.split(script_path)[0]


class EngineContext(object):
  '''
  Portable context for simulator engines.
  Mainly carries around the list of characters.
  '''

  def __init__(self, groups=[], round=0, phase=0):
    # initialize groups
    self._groups = groups
    if len(self._groups) < 2:
      raise ValueError("Must have at least two groups")
    # initialize characters
    self._characters = []
    for group in groups:
      if len(group) < 1:
        raise ValueError('A group must contain at least one character')
      for character in group:
        self._characters.append(character)
    if len(self._characters) < 2:
      raise ValueError("Must have at least two characters")
    # features for analysis
    self._features = TrialFeatures()
    # initialize timing
    self._round = round
    self._phase = phase
    # default probability chart data paths
    self._data_path_probabilities_rerolled = os.path.join(script_dirpath, 'probabilities_rerolled.txt')
    self._data_path_probabilities_not_rerolled = os.path.join(script_dirpath, 'probabilities_not_rerolled.txt')

  def characters(self):
    return self._characters

  def groups(self):
    return self._groups

  def features(self):
    return self._features

  def load_probability_data(self):
    '''
    load_probability_data()

    Loads probability data to help calculate the probability of making rolls.
    '''
    self._probabilities = {}
    self._mean_rolls = { True: {}, False: {} }
    self._probabilities[True] = self._load_probability_file(self._data_path_probabilities_rerolled)
    self._probabilities[False] = self._load_probability_file(self._data_path_probabilities_not_rerolled)
    self._load_mean_roll_data(True)
    self._load_mean_roll_data(False)

  def _load_probability_file(self, path):
    data = {}
    with open(path, 'r') as f:
      for line in f:
        if line.startswith('Rolled'):
          continue
        line = line.strip()
        tokens = line.split('\t')
        roll = tokens[0]
        probabilities = [float(p) for p in tokens[1:-1]]
        probabilities.insert(0, 1.00)
        data[roll] = probabilities
    return data

  def _load_mean_roll_data(self, explode):
    for roll in self._probabilities[explode].keys():
      prev_i = 0
      for i, p in enumerate(self._probabilities[explode][roll]):
        if p < 0.50:
          self._mean_rolls[explode][roll] = prev_i
          break
        prev_i = i

  def mean_roll(self, rolled, kept, explode=True):
    '''
    mean_roll(rolled, kept, explode=True) -> int
      rolled (int): rolled dice
      kept (int): kept dice
      explode (bool): whether or not tens reroll

    Returns the mean result of a roll with the given parameters.
    '''
    rolled, kept, bonus = normalize_roll_params(rolled, kept)
    roll_str = '{}k{}'.format(rolled, kept)
    return self._mean_rolls[explode][roll_str] + bonus

  def next_phase(self):
    if (self._phase == 10):
      raise RuntimeError('Cannot go to next phase after 10')
    self._phase += 1

  def next_round(self):
    self._round += 1
    self._phase = 0

  def phase(self):
    return self._phase

  def p(self, x, rolled, kept, explode=True):
    '''
    p(x, explode=True) -> float
      x (int): target number
      rolled (int): number of rolled dice
      kept (int): number of kept dice
      explode (bool): whether or not tens reroll

    Return the probability of rolling Target Number x with the given parameters.
    '''
    roll_str = '{}k{}'.format(rolled, kept)
    max_x = len(self._probabilities[explode][roll_str]) - 1
    if x > max_x:
      return self._probabilities[explode][roll_str][max_x]
    else:
      return self._probabilities[explode][roll_str][x]

  def reevaluate_initiative(self):
    max_actions = max([len(character.actions()) for character in self._characters if character.is_fighting()])
    self._characters.sort(key=lambda character: character.initiative_priority(max_actions))

  def reset(self):
    self._features.clear()
    self._phase = 0
    self._round = 0
    for character in self._characters:
      character.reset()

  def round(self):
    return self._round

  def time(self):
    return (self._round, self._phase)

  def update_status(self, event):
    # TODO: support more than two groups
    for i, group in enumerate(self._groups):
      fighting = False
      for character in group:
        if character.is_fighting():
          fighting = True
          break
      if not fighting:
        if i == 0:
          self.features().observe_winner(-1)
        else:
          self.features().observe_winner(1)
        raise CombatEnded('Combat is over')

