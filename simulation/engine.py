
from abc import abstractmethod

from simulation.events import ActionEvent, EndOfPhaseEvent, EndOfRoundEvent, InitiativeChangedEvent, NewPhaseEvent, NewRoundEvent, StatusEvent, TakeActionEvent
from simulation.exceptions import CombatEnded
from simulation.log import logger

class Engine(object):
  '''
  Generic event loop for the L7R combat simulator.
  This runs a loop that runs events on characters in the appropriate order.
  '''

  def __init__(self, context):
    self._context = context
    self._history = []

  def context(self):
    return self._context

  def event(self, event):
    logger.debug('Got {} event'.format(event.name))
    self._history.append(event)
    # status events might end the run
    if isinstance(event, StatusEvent):
      logger.debug('Evaluating status event')
      self._context.update_status(event)
    # take action events require reevaluating initiative priority
    if isinstance(event, InitiativeChangedEvent) or isinstance(event, TakeActionEvent):
      logger.debug('Reevaluating initiative priority')
      self._context.reevaluate_initiative()
    if hasattr(event, 'play'):
      # event play method is a generator for more events
      for next_event in event.play():
        self.event(next_event)
    else:
      # play event on each character in initiative order
      for character in self._context.characters():
        reaction = character.event(event, self._context)
        if reaction is not None:
          self.event(reaction)

  def get_history(self):
    return self._history

  def reset(self):
    self._history.clear()
    self._context.reset()

  @abstractmethod
  def run(self):
    raise NotImplementedError()


class CombatEngine(Engine):
  '''
  Class to represent the combat event loop.
  Combat timing is broken up into rounds.
  Each round is timed in eleven phases, numbered 0 through 10.
  In each phase, each character is given the option to act in initiative order.
  Characters can choose to take actions, which are also resolved as a series of events.
  During combat, characters may lose consciousness, die, surrender, or flee.
  The loop ends when only one side is still fighting.
  '''

  def __init__(self, context):
    super().__init__(context)

  def run(self):
    while (True):
      try:
        self.run_round()
      except CombatEnded:
        break
      except KeyboardInterrupt:
        break

  def run_round(self):
    logger.debug('Starting Round {}'.format(self.context().round()))
    self.context().features().observe_round()
    self.event(NewRoundEvent(self.context().round()))
    if self.context().phase() != 0:
      raise RuntimeError('New round should begin in phase 0')
    while True:
      logger.debug('Starting Phase {}'.format(self.context().phase()))
      self.context().features().observe_phase()
      self.event(NewPhaseEvent(self.context().phase()))
      self.event(EndOfPhaseEvent(self.context().phase()))
      if self.context().phase() < 10:
        self.context().next_phase()
      else:
        break
    self.event(EndOfRoundEvent(self.context().round()))
    self.context().next_round()

