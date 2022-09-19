
from abc import abstractmethod

from simulation.events import ActionEvent, EndOfPhaseEvent, EndOfRoundEvent, NewPhaseEvent, NewRoundEvent, StatusEvent, TakeActionEvent
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

  def event(self, event):
    logger.debug('Got {} event'.format(event.name))
    self._history.append(event)
    # status events might end the run
    if isinstance(event, StatusEvent):
      logger.debug('Evaluating status event')
      self._context.update_status(event)
    # take action events require reevaluating initiative priority
    if isinstance(event, TakeActionEvent):
      logger.debug('Reevaluating initiative priority')
      self._context.reevaluate_initiative()
    if hasattr(event, 'run'):
      # runnable events run their own engine
      # TODO: implement this
      for next_event in event.run():
        self.event(next_event)
    else:
      # play event on each character in initiative order
      for character in self._context.characters():
        reaction = character.event(event, self._context)
        if reaction is not None:
          self.event(reaction)

  def get_history(self):
    return self._history

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

  Here is an example combat between Akodo (A) and Bayushi (B):

  The CombatEngine starts in Round 1, Phase 0. It plays a new_round event.

  event: new_round(1)
    This event is played on each character.
    Akodo's new_round listener rolls initiative.
    Akodo gets actions in (1, 3, 5).
    Bayushi's new_round listener rolls initiative.
    Bayushi gets actions in (2, 3, 3).
    The engine sorts the characters by initiative priority and finds priority for Akodo.

  The CombatEngine advances to Phase 0 and plays a new_phase event.

  event: new_phase(0)
    Akodo's new_phase listener calls his ActionStrategy.
    Akodo's ActionStrategy finds that he does not have an action and shouldn't interrupt, so he does nothing.
    Bayushi's new_phase listener calls his ActionStrategy.
    Bayushi's ActionStrategy finds that he does not have an action and shouldn't interrupt, so he does nothing.

  The CombatEngine advances to Phase 1 and plays a new_phase event.

  event: new_phase(1)
    Akodo's new_phase listener calls his ActionStrategy
    Akodo's ActionStrategy tries his AttackStrategy
    Akodo's AttackStrategy recommends an AttackAction on Bayushi.
    Akodo's AttackAction runs an AttackEngine.

  The AttackEngine plays a declare_attack event.

  event: declare_attack
    The engine handles a declare action event by reevaluating initiative priority. Now Bayushi has priority.
    Bayushi's listener for a declare_attack action calls his ParryStrategy.
    Bayushi's ParryStrategy does not recommend a Parry action because he is not damaged enough to warrant a preemptive Parry.
    Akodo's listener for a declare_attack action calls his ParryStrategy.
    Akodo's ParryStrategy does not recommend a Parry action because he is the attacker.
  
  The AttackEngine uses the AttackAction to roll the attack. The roll is around average.
  The AttackEngine plays an attack_rolled event.

  event: attack_rolled
    Bayushi's listener for attack_rolled calls his ParryStrategy.
    Bayushi's ParryStrategy does not recommend a Parry action because the roll is not bad enough to warrant a Parry.
    Akodo's listener for an AttackRolled event calls his ParryStrategy.
    Akodo's ParryStrategy does not recommend a Parry because he is the attacker.

  The AttackEngine uses the AttackAction to roll damage.
  The AttackEngine plays an lw_damage event.

  event: lw_damage
    Bayushi's listener for lw_damage rolls his Wound Check and takes 1 SW.
    Akodo's listener for lw_damage does not respond because he is not the target.

  The AttackEngine is done, and execution returns to the CombatEngine.
  The CombatEngine resumes playing the new_phase(1) event on characters.

  event: new_phase(1) (resumed)
    Bayushi's new_phase listener calls his ActionStrategy.
    Bayushi's ActionStrategy tries his AttackStrategy.
    Bayushi's AttackStrategy does not recommend an interrupt action, so he does nothing.

  The CombatEngine advances to Phase 2 and plays a new_phase event.

  event: new_phase(2)
    Bayushi's new_phase listener tries his ActionStrategy.
    Bayushi's ActionStrategy tries his AttackStrategy.
    Bayushi's AttackStrategy recommends a FeintAction on Akodo.
    Bayushi's FeintAction runs an AttackEngine.

  The AttackEngine plays a declare_attack event.
  
  event: declare_attack
    Bayushi's listener for declare_attack uses his ParryStrategy.
    Bayushi's ParryStrategy does not recommend a Parry action because he is the attacker.
    Akodo's listener for declare_attack uses his ParryStrategy.
    Akodo's ParryStrategy does not recommend a Parry action because he is not damaged enough to warrant a preemptive Parry.

  The AttackEngine uses the FeintAction to roll the feint. The feint roll is around average.
  The AttackEngine plays an attack_rolled event.

  event: attack_rolled
    Bayushi's listener for attack_rolled calls his ParryStrategy.
    Bayushi's ParryStrategy does not recommend a Parry action because he is the attacker.
    Akodo's listener for an AttackRolled event calls his ParryStrategy.
    Akodo's ParryStrategy does not recommend a Parry because the roll is not high enough to warrant a Parry.

  The AttackEngine plays a successful_feint
  The AttackEngine uses the FeintAction, which finds that Bayushi should roll damage for a successful Feint.
  The AttackEngine uses the FeintAction to roll damage.
  The AttackEngine plays a lw_damage event.

  event: lw_damage
    Bayushi's listener for lw_damage does not respond because he is not the target.
    Akodo's listener for lw_damage rolls his Wound Check, and he keeps some Light Wounds.

  The AttackEngine is done, and execution returns to the CombatEngine.
 to roll for damage. The FeintAction checks and finds that Bayushi should
  roll damage on Feints, so it does. FeintAction finds that Bayushi does damage on Feints, so it rolls damage.
Bayushi is only 2nd Dan, so he doesn't get to roll damage on this Feint.
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
    logger.debug('Starting Round {}'.format(self._context.round()))
    self.event(NewRoundEvent(self._context.round()))
    if self._context.phase() != 0:
      raise RuntimeError('New round should begin in phase 0')
    while True:
      logger.debug('Starting Phase {}'.format(self._context.phase()))
      self.event(NewPhaseEvent(self._context.phase()))
      self.event(EndOfPhaseEvent(self._context.phase()))
      if self._context.phase() < 10:
        self._context.next_phase()
      else:
        break
    self.event(EndOfRoundEvent(self._context.round()))
    self._context.next_round()


 
