#!/usr/bin/env python3

#
# modifiers.py
# Author: Patrick Bannister (ptbannister@gmail.com)
# Implement modifiers (flat bonuses or penalties to rolls) that can expire in response to events.
#


class Modifier(object):
  '''
  Class for modifiers (bonuses or penalties) that are skill-specific and have an expiration.
  '''
  def __init__(self, subject, target, skill, adjustment):
    self._subject = subject
    self._target = target
    self._skill = skill
    self._adjustment = adjustment
    self._listeners = {}

  def apply(self, subject, target, skill):
    '''
    apply(subject, target, skill) -> int

    Returns the effect of this modifier on a skill or thing,
    or zero if it doesn't apply.
    '''
    if self.skill() == skill or self.skill() == 'any':
      if self.subject() is None or self.subject() == subject:
        if self.target() is None or self.target() == target:
          return self.adjustment()
    return 0

  def event(self, event, context):
    if event.name in self._listeners.keys():
      return self._listeners[event.name].handle(self.subject(), event, context)

  def adjustment(self):
    return self._adjustment

  def register_listener(self, listener, event_name):
    self._listeners[event_name] = listener

  def skill(self):
    return self._skill

  def subject(self):
    return self._subject

  def target(self):
    return self._target


# the standard penalty for parrying on behalf of another character
PARRY_OTHER_PENALTY = Modifier(None, None, 'parry_other', -10)


class FreeRaise(Modifier):
  def __init__(self, skill):
    super().__init__(None, None, skill, 5)

  def apply(self, skill):
    if self.skill() == skill:
      return 5

