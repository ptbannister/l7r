#!/usr/bin/env python3

#
# modifier_listeners.py
# Author: Patrick Bannister (ptbannister@gmail.com)
#
# A class that can respond to events to expire modifiers.
# These are a completely separate object from Listener.
# With normal Listeners, the handle method is a generator.
# With ModifierListeners, the handle method determines whether or not to remove the modifier.
#

from abc import ABC, abstractmethod

from simulation.events import AttackFailedEvent, AttackSucceededEvent, EndOfRoundEvent
from simulation.log import logger
from simulation.modifiers import Modifier
from simulation.skills import ATTACK_SKILLS


class ModifierListener(ABC):
  '''
  An observer that may be registered on a Modifier to make it expire in response to some event.
  '''
  @abstractmethod
  def handle(self, character, event, context):
    '''
    Evaluate whether the modifier should expire, and remove it from the character if so.
    '''
    pass

  @abstractmethod
  def modifier(self):
    '''
    Get the modifier associated with this ModifierListener.
    '''
    pass


class BaseModifierListener(ModifierListener):
  def __init__(self, modifier):
    self._modifier = modifier

  def handle(self, character, event, context):
    raise NotImplementedError()

  def modifier(self):
    return self._modifier


class ExpireAfterNextAttackListener(BaseModifierListener):
  '''
  Expire a modifier after the next attack against the character.
  '''
  def handle(self, character, event, context):
    if isinstance(event, AttackFailedEvent) or isinstance(event, AttackSucceededEvent):
      if character == event.action.target():
        character.remove_modifier(self.modifier())


class ExpireAfterNextAttackByCharacterListener(BaseModifierListener):
  '''
  Expire a modifier after the next attack by a specific attacker against the character.
  '''
  def __init__(self, modifier, attacker):
    super().__init__(modifier)
    self._attacker = attacker

  def handle(self, character, event, context):
    if isinstance(event, AttackFailedEvent) or isinstance(event, AttackSucceededEvent):
      if character == event.action.target() and self._attacker == event.action.subject():
        character.remove_modifier(self.modifier())


class ExpireAtEndOfRoundListener(BaseModifierListener):
  '''
  Expire a modifier at the end of the current round.
  '''
  def handle(self, character, event, context):
    if isinstance(event, EndOfRoundEvent):
      character.remove_modifier(self.modifier())

