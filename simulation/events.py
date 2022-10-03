#!/usr/bin/env python3

#
# events.py
# Author: Patrick Bannister
# Events for the L7R combat simulator.
#


class Event(object):
  '''
  Events capture a moment in L7R combat mechanics when a character
  is affected, or a decision must be made.
  Examples:
   * new phase: characters with actions should decide what to do
   * attack rolled: characters should decide whether to parry
   * light wounds: character might decide to spend VP on wound check

  Events are basically messages. They should be treated as immutable.
  Other classes should never modify an event!

  Since we have the convention that events are immutable, we can also
  have the convention that other classes are expected to access members
  of events directly.

  Some events have a **play** method. This is a generator method that
  yields more events. This should only be done in exceptional
  circumstances.

  Every event can have different fields depending on the event,
  but there was some effort to have a kind of consistent vocabulary.
  **Subject**: if an event involves a character who is actively doing
               something, the **subject** of the event is the active
               character.
  **Target**:  if an event involves a character who is the direct
               object of something - such as being attacked, or taking
               damage - then the **target** of the event is that
               character.
  **Damage**:  events about damage, whether they're for receiving light
               wound, receiving serious wounds, or making a wound check,
               have a **damage** member for the amount of damage.
  '''
  def __init__(self, name):
    self.name = name


class TimingEvent(Event):
  pass

class NewRoundEvent(TimingEvent):
  def __init__(self, round):
    super().__init__('new_round')
    self.round = round

class NewPhaseEvent(TimingEvent):
  def __init__(self, phase):
    super().__init__('new_phase')
    self.phase = phase

class EndOfPhaseEvent(TimingEvent):
  def __init__(self, phase):
    super().__init__('end_of_phase')
    self.phase = phase

class EndOfRoundEvent(TimingEvent):
  def __init__(self, round):
    super().__init__('end_of_round')
    self.round = round


class InitiativeChangedEvent(Event):
  def __init__(self):
    super().__init__('initiative_changed')


class ActionEvent(Event):
  def __init__(self, name, action):
    super().__init__(name)
    self.action = action

class TakeActionEvent(ActionEvent):
  def __init__(self, name, action):
    super().__init__(name, action)


class TakeAttackActionEvent(TakeActionEvent):
  def __init__(self, action):
    super().__init__('take_attack', action)

  def play(self):
    yield self._declare_attack()
    yield self._roll_attack()
    if self.action.parried():
      yield self._failed()
      return
    if self.action.is_hit():
      yield self._succeeded()
      direct_damage = self._direct_damage()
      if direct_damage is not None:
        yield direct_damage
      if self.action.target().is_fighting():
        yield self._roll_damage()
    else:
      yield self._failed()

  def _declare_attack(self):
    return AttackDeclaredEvent(self.action)
  
  def _direct_damage(self):
    return self.action.direct_damage()

  def _failed(self):
    return AttackFailedEvent(self.action)

  def _roll_attack(self):
    attack_roll = self.action.roll_attack()
    return AttackRolledEvent(self.action, attack_roll)

  def _roll_damage(self):
    damage_roll = self.action.roll_damage()
    return LightWoundsDamageEvent(self.action.target(), damage_roll)

  def _succeeded(self):
    return AttackSucceededEvent(self.action)


class TakeParryActionEvent(TakeActionEvent):
  def __init__(self, action):
    super().__init__('take_parry', action)

  def play(self):
    yield self._declare_parry()
    yield self._roll_parry()
    if self.action.is_success():
      yield self._succeeded()
    else:
      yield self._failed()
    
  def _declare_parry(self):
    declaration = ParryDeclaredEvent(self.action)
    self.action.set_attack_parry_declared(declaration)
    return declaration

  def _failed(self):
    return ParryFailedEvent(self.action)

  def _roll_parry(self):
    parry_roll = self.action.roll_parry()
    self.action.set_attack_parry_attempted()
    return ParryRolledEvent(self.action, parry_roll)

  def _succeeded(self):
    self.action.set_attack_parried()
    return ParrySucceededEvent(self.action)


class ShibaTakeParryEvent(TakeParryActionEvent):
  def play(self):
    yield self._declare_parry()
    yield self._roll_parry()
    if self.action.is_success():
      yield self._succeeded()
    else:
      yield self._failed()
    yield self._roll_damage()

  def _roll_damage(self):
    rolled = self._action.subject().skill('attack') * 2
    damage_roll = self._action.subject().roll_damage(rolled, 1)
    return LightWoundsDamageEvent(self._action.target(), damage_roll)


class AttackDeclaredEvent(ActionEvent):
  def __init__(self, action):
    super().__init__('attack_declared', action)

class AttackRolledEvent(ActionEvent):
  def __init__(self, action, roll):
    super().__init__('attack_rolled', action)
    self.roll = roll

class AttackSucceededEvent(ActionEvent):
  def __init__(self, action):
    super().__init__('attack_succeeded', action)

class AttackFailedEvent(ActionEvent):
  def __init__(self, action):
    super().__init__('attack_failed', action)


class ParryDeclaredEvent(ActionEvent):
  def __init__(self, action):
    super().__init__('parry_declared', action)

class ParryPredeclaredEvent(ActionEvent):
  def __init__(self, action):
    super().__init__('parry_predeclared', action)

class ParryRolledEvent(ActionEvent):
  def __init__(self, action, roll):
    super().__init__('parry_succeeded', action)
    self.roll = roll

class ParrySucceededEvent(ActionEvent):
  def __init__(self, action):
    super().__init__('parry_succeeded', action)

class ParryFailedEvent(ActionEvent):
  def __init__(self, action):
    super().__init__('parry_failed', action)


class DamageEvent(Event):
  def __init__(self, name, target, damage):
    super().__init__(name)
    self.target = target
    self.damage = damage

class LightWoundsDamageEvent(DamageEvent):
  def __init__(self, target, damage):
    super().__init__('lw_damage', target, damage)

class SeriousWoundsDamageEvent(DamageEvent):
  def __init__(self, target, damage):
    super().__init__('sw_damage', target, damage)

class TakeSeriousWoundEvent(DamageEvent):
  def __init__(self, target, damage):
    super().__init__('take_sw', target, damage)


class StatusEvent(Event):
  def __init__(self, name, subject):
    super().__init__(name)
    self.subject = subject

class DeathEvent(StatusEvent):
  def __init__(self, subject):
    super().__init__('death', subject)

class SurrenderEvent(StatusEvent):
  def __init__(self, subject):
    super().__init__('surrender', subject)

class UnconsciousEvent(StatusEvent):
  def __init__(self, subject):
    super().__init__('unconscious', subject)


class WoundCheckEvent(Event):
  def __init__(self, name, subject, damage):
    super().__init__(name)
    self.subject = subject
    self.damage = damage

class WoundCheckDeclaredEvent(WoundCheckEvent):
  def __init__(self, subject, damage, vp=0):
    super().__init__('wound_check_declared', subject, damage)
    self.vp = vp

class WoundCheckFailedEvent(WoundCheckEvent):
  def __init__(self, subject, damage, roll):
    super().__init__('wound_check_failed', subject, damage)
    self.roll = roll

class WoundCheckRolledEvent(WoundCheckEvent):
  def __init__(self, subject, damage, roll, vp=0):
    super().__init__('wound_check_rolled', subject, damage)
    self.roll = roll

class WoundCheckSucceededEvent(WoundCheckEvent):
  def __init__(self, subject, damage, roll):
    super().__init__('wound_check_succeeded', subject, damage)
    self.roll = roll


class SpendResourcesEvent(Event):
  def __init__(self, name, subject, amount):
    super().__init__(name)
    self.subject = subject
    self.amount = amount

class SpendAdventurePointsEvent(SpendResourcesEvent):
  def __init__(self, subject, amount):
    super().__init__('spend_ap', subject, amount)

class SpendVoidPointsEvent(SpendResourcesEvent):
  def __init__(self, subject, amount):
    super().__init__('spend_vp', subject, amount)

  
