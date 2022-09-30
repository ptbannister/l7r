

class Modifier(object):
  '''
  Class for modifiers (bonuses or penalties) that are skill-specific and have an expiration.
  '''
  def __init__(self, subject, target, skill, adjustment):
    self._subject = subject
    self._target = target
    self._skill = skill
    self._adjustment = modifier
    self._listeners = {}

  def apply(self, subject, target, skill, context):
    '''
    apply(subject, target, skill, context) -> int

    Returns the effect of this modifier on a skill or thing, or zero if it doesn't apply.
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


class FreeRaise(Modifier):
  def __init__(self, skill):
    super().__init__(None, None, skill, 5)

  def apply(self, skill):
    if self.skill() == skill:
      return 5


class ModifierListener(Listener):
  def __init__(self, modifier):
    self._modifier = modifier

  def matches_action_event(self, character, event):
    if event.action.subject() == character:
      if self.modifier().subject() is None or self.modifier().subject() == event.action.subject():
        if self.modifier().target() is None or self.modifier().target() == event.action.target():
          if self.modifier().skill() == 'any' or self.modifier().skill() == event.skill:
            return True
    return False

  def modifier(self):
    return self._modifier

 
class ExpireAfterNextAttackListener(ModifierListener):
  def handle(self, character, event, context):
    if isinstance(event, AttackFailedEvent) or isinstance(event, AttackSucceededEvent):
      if self.matches_action_event(character, event):
        character.remove_modifier()(self.modifier())

