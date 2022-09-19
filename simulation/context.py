
from simulation.exceptions import CombatEnded


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
    # initialize timing
    self._round = round
    self._phase = phase

  def characters(self):
    return self._characters

  def next_phase(self):
    if (self._phase == 10):
      raise RuntimeError('Cannot go to next phase after 10')
    self._phase += 1

  def next_round(self):
    self._round += 1
    self._phase = 0

  def phase(self):
    return self._phase

  def reevaluate_initiative(self):
    max_actions = max([len(character.actions()) for character in self._characters if character.is_fighting()])
    self._characters.sort(key=lambda character: character.initiative_priority(max_actions))

  def round(self):
    return self._round

  def time(self):
    return (self._round, self._phase)

  def update_status(self, event):
    # TODO: support more than two groups
    for group in self._groups:
      fighting = False
      for character in group:
        if character.is_fighting():
          fighting = True
          break
      if not fighting:
        raise CombatEnded('Combat is over')

