

class Action(object):
  def __init__(self, subject, target, ring, skill):
    self._subject = subject
    self._target = target
    self._ring = ring
    self._skill = skill

  def ring(self):
    return self._ring

  def skill(self):
    return self._skill

  def subject(self):
    return self._subject

  def target(self):
    return self._target


class AttackAction(Action):
  def __init__(self, subject, target, skill='attack', vp=0, ap=0, weapon_rolled=4, weapon_kept=2):
    super().__init__(subject, target, 'fire', skill)
    self._ap = ap
    self._attack_roll = None
    self._damage_roll = None
    self._parries_declared = []
    self._parries_predeclared = []
    self._parried = False
    self._parry_attempted = False
    self._vp = 0
    self._weapon_rolled = weapon_rolled
    self._weapon_kept = weapon_kept

  def add_parry_declared(self, event):
    self._parries_declared.append(event)

  def add_parry_predeclared(self, event):
    self._parries_predeclared.append(event)
    self.add_parry_declared(event)

  def calculate_extra_damage_dice(self):
    if self.parry_attempted():
      return 0
    else:
      return (self._attack_roll - self.tn()) // 5

  def is_hit(self):
    tn = self._target.base_to_hit_tn()
    return self._attack_roll >= tn and not self.parried()

  def parried(self):
    return self._parried

  def parry_attempted(self):
    return self._parry_attempted

  def parries_declared(self):
    return self._parries_declared

  def roll_attack(self):
    self._attack_roll = self._subject.roll_skill(self.ring(), self.skill(), self._vp, self._ap)
    return self._attack_roll

  def roll_damage(self):
    extra_rolled = self.calculate_extra_damage_dice()
    self._damage_roll = self._subject.roll_damage(self.skill(), extra_rolled, self._weapon_rolled, self._weapon_kept)
    return self._damage_roll

  def set_parry_attempted(self):
    self._parry_attempted = True

  def set_parried(self):
    self._parried = True

  def tn(self):
    return self._target.base_to_hit_tn() 


class ParryAction(Action):
  def __init__(self, subject, target, attack, predeclared=False, vp=0, ap=0):
    super().__init__(subject, target, 'air', 'parry')
    self._ap = 0
    self._attack = attack
    self._parry_roll = 0
    self._predeclared = predeclared
    self._vp = 0

  def is_success(self):
    return self._parry_roll >= self._attack._attack_roll

  def roll_parry(self):
    self._parry_roll = self._subject.roll_skill(self.ring(), self.skill(), self._vp, self._ap)
    return self._parry_roll

  def set_attack_parry_declared(self, event):
    self._attack.add_parry_declared(event)

  def set_attack_parried(self):
    self._attack.set_parried()

  def set_attack_parry_attempted(self):
    self._attack.set_parry_attempted()

