
class Event(object):
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

  def run(self):
    yield self._declare_attack()
    yield self._roll_attack()
    # TODO: maybe need to run a parry engine here
    if self.action.parried():
      return self._failed()
    if self.action.is_hit():
      yield self._succeeded()
      yield self._roll_damage()
    else:
      yield self._failed()

  def _declare_attack(self):
    return AttackDeclaredEvent(self.action)
  
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

class ParrySucceededEvent(ActionEvent):
  def __init__(self, action):
    super().__init__('parry_succeeded', action)

class ParryFailedEvent(ActionEvent):
  def __init__(self, action):
    super().__init__('parry_failed', action)


class DamageEvent(Event):
  def __init__(self, name, target, amount):
    super().__init__(name)
    self.target = target
    self.amount = amount

class LightWoundsDamageEvent(DamageEvent):
  def __init__(self, target, amount):
    super().__init__('lw_damage', target, amount)

class SeriousWoundsDamageEvent(DamageEvent):
  def __init__(self, target, amount):
    super().__init__('sw_damage', target, amount)

class TakeSeriousWoundEvent(DamageEvent):
  def __init__(self, target, amount):
    super().__init__('take_sw', target, amount)


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
  def __init__(self, subject, damage, roll):
    super().__init__('wound_check_rolled', subject, damage)
    self.roll = roll

class WoundCheckSucceededEvent(WoundCheckEvent):
  def __init__(self, subject, damage, roll):
    super().__init__('wound_check_succeeded', subject, damage)
    self.roll = roll

