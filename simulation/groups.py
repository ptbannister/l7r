#!/usr/bin/env python3

from collections.abc import MutableSet

from simulation.character import Character
from simulation.knowledge import Knowledge


class Group(MutableSet):
  '''
  Class to represent a group of characters, used in a combat that is more than one-on-one.
  Provides features to help characters tell friend from foe and to create group knowledge.
  '''
  def __init__(self, characters=[]):
   self._characters = {}
   for character in characters:
     character.set_group(self)
     self._characters[character.name()] = character
   self._knowledge = Knowledge()

  def add(self, character):
    self._characters[character.name()] = character

  def clear(self):
    self._characters.clear()
    self._knowledge = Knowledge()

  def discard(self, character):
      self._characters.pop(character.name())

  def friends_near_defeat(self, context):
    '''
    friends_near_defeat(context) -> list of Characters
      context (EngineContext): context

    Return a list of characters in this group who are still fighting but near defeat.
    '''
    return [character for character in self._characters.values() if character.sw_remaining() < 2 and character.is_fighting()]

  def friends_with_actions(self, context):
    '''
    friends_with_actions(context) -> list of Characters
      context (EngineContext): context

    Return a list of characters in this group who have actions and are still fighting.
    '''
    return [character for character in self._characters.values() if character.has_action(context) and character.is_fighting()]

  def __contains__(self, character):
    if isinstance(character, Character):
      return character.name() in self._characters.keys()
    elif isinstance(character, str):
      return character in self._characters.key()
    else:
      raise NotImplementedError('Cannot check if Group contains object of type {}', type(character))

  def __eq__(self, other):
    if self is other:
      return True
    elif not isinstance(other, Group):
      return False
    else:
      # TODO: make sure this works correctly
      return self._characters == other._characters

  def __iter__(self):
    for character in self._characters.values():
      yield character

  def __len__(self):
    return len(self._characters)

