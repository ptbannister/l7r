
from abc import ABC, abstractmethod
import itertools
import math

from simulation import actions, events
from simulation.knowledge import TheoreticalCharacter
from simulation.log import logger
from simulation.roll import normalize_roll_params

class Strategy(ABC):
  '''
  Class that can choose between possible decisions to respond to an Event.
  The Strategy and Listener classes both respond to an Event by
  optionally returning another Event, which begs the question, why
  not just put strategy logic into Listeners?
  The idea behind separating Listener and Strategy is to keep the two classes simple.
  Listener is responsible for knowing when to mutate the Character's state
  (taking damage, spending resources, etc). The Strategy implements
  complex logic to choose between possible courses of action.
  Mixing the two classes would result in big Listener classes that
  would contain too much complexity. It would be difficult to write
  such a big class, or to test it effectively.
  Isolating decision making logic in the Strategy class also helps
  deal with the fact that different kinds of characters will have
  different strategies around certain aspects of their behavior, and
  it will be easier to write a lot of different little Strategy classes
  than it would be to write several big Listener classes.
  '''
  @abstractmethod
  def recommend(self, character, event, context):
    '''
    recommend(character, event, context) -> Event or None
      character (Character): Character deciding how to respond to the Event
      event (Event): an Event requiring a decision about how to act
      context (EngineContext): context about other Characters, groups, timing, etc

    Makes a decision about whether and how to respond to an Event.
    This should be used to deal with decisions like whether to spend
    Void Points or school abilities, or whether to parry an attack,
    or whether to hold actions or spend them immediately, etc.
    '''
    pass


class AlwaysAttackActionStrategy(Strategy):
  def recommend(self, character, event, context):
    if isinstance(event, events.YourMoveEvent):
      # try to attack if action available
      # TODO: evaluate whether to interrupt
      if character.has_action(context):
        yield from character.attack_strategy().recommend(character, event, context)
      else:
        yield events.NoActionEvent(character)


class HoldOneActionStrategy(Strategy):
  def recommend(self, character, event, context):
    if isinstance(event, events.YourMoveEvent):
      # try to hold an action in reserve until Phase 10
      if character.has_action(context):
        available_actions = [action for action in character.actions() if action <= context.phase()]
        if len(available_actions) > 1 or context.phase() == 10:
          yield from character.attack_strategy().recommend(character, event, context)
        else:
          logger.debug('{} is holding an action'.format(character.name()))
          yield events.HoldActionEvent(character)
      else:
        yield events.NoActionEvent(character)


class BaseAttackStrategy(Strategy):
  def find_target(self, subject, skill, context):
    '''
    find_target(subject, skill, context) -> Character
       subject (Character): character who is finding a target to attack
       skill (str): attack skill being used
       context (EngineContext): context
  
    Returns a Character who is a good target to attack, or returns None if no good target is found.
    '''
    targets = []
    for other_character in context.characters():
      # don't try to fight yourself or your buddies
      if other_character not in subject.group():
        # don't stab the corpses
        if other_character.is_fighting():
          # can I hit this character with this skill?
          proxy_target = TheoreticalCharacter(subject.knowledge(), other_character)
          action = self.get_attack_action(subject, proxy_target, skill)
          (rolled, kept, modifier) = subject.get_skill_roll_params(other_character, skill)
          # TODO: use a threshold
          p_hit = context.p(action.tn() - modifier, rolled, kept)
          targets.append((other_character, p_hit))
    # sort targets in order of probability of hitting
    # TODO: prefer certain targets because they are closer to defeat, or they are more dangerous, etc
    targets.sort(key=lambda t: t[1], reverse=True)
    # return the easiest target to hit
    if len(targets) > 0:
      return targets[0][0]
    else:
      return None
  
  def get_attack_action(self, subject, target, skill, vp=0):
    if skill == 'attack':
      return actions.AttackAction(subject, target, skill, vp)
    elif skill == 'counterattack':
      return actions.AttackAction(subject, target, skill, vp)
    elif skill == 'double attack':
      return actions.DoubleAttackAction(subject, target, vp)
    elif skill == 'feint':
      return actions.FeintAction(subject, target, vp)
    elif skill == 'lunge':
      return actions.LungeAction(subject, target, vp)

  def get_expected_kept_damage_dice(self, subject, target, skill, context, ap, vp):
    '''
    get_expected_damage_params(subject, target, skill, context, ap, vp) -> int
      subject (Character): character who would be the attacker
      target (Character): character who would be the target
      skill (str): name of the skill to be used to attack
      context (EngineContext): context
      ap (int): number of Adventure Points to spend on this attack
      vp (int): number of Void Points to spend on this attack
  
    Return the expected kept damage dice for an attack given the inputs.
    '''
    theoretical_target = TheoreticalCharacter(subject.knowledge(), target)
    speculative_action = self.get_attack_action(subject, theoretical_target, skill, vp)
    # how many kept damage dice are expected?
    attack_rolled, attack_kept, attack_mod = subject.get_skill_roll_params(target, skill, vp)
    expected_attack_roll = context.mean_roll(attack_rolled, attack_kept) + attack_mod + (5 * ap)
    expected_extra_rolled = speculative_action.calculate_extra_damage_dice(expected_attack_roll, subject.knowledge().tn_to_hit(target))
    damage_rolled, damage_kept, damage_bonus = subject.get_damage_roll_params(target, skill, expected_extra_rolled)
    return damage_kept
  
  def optimize_attack(self, subject, target, skill, context):
    '''
    optimize_attack(subject, target, skill, context) -> AttackAction
  
    Returns an AttackAction optimized to spend VP for more damage.
  
    Optimizing an attack is about getting more damage for the minimum expenditure of resources.
    Attacks get an extra rolled damage die for every increment of 5 by which they exceed the TN to hit.
    A base damage roll, with no extra rolled dice, normally keeps 2 dice.
  
    It helps to understand the curve of average damage rolls:
     6k2: 18 (Base damage for characters with 2 Fire)
     7k2: 19 (Base damage for 3 Fire)
     8k2: 21 (Base damage for 4 Fire)
     9k2: 22 (Base damage for 5 Fire)
    10k2: 23 (Base damage for 6 Fire)
    10k3: 31
    10k4: 38
    10k5: 44
    10k6: 49
    10k7: 53
    10k8: 56
    10k9: 59
    10k10: 60
  
    The marginal benefit of extra rolled damage dice is a bell curve.
    The big margins come between 10k3 and 10k6.
  
    This function is designed to find an acceptable expenditure of resources
    to reach extra kept damage dice if possible.
    '''
    ap, vp = 0, 0
    # establish how many ap and vp we can and want to spend
    # TODO: write AdventurePointStrategy and VoidPointStrategy
    max_ap_spend = min(subject.ap(), 2)
    possible_ap_spends = [ap_spend for ap_spend in range(subject.ap() + 1)]
    # character should be conservative with vp on attacks, unless they are tvp
    # mostly need to save vp for wound checks
    # it's too easy for a parry to wipe out the gains of vp spent on attacks
    max_vp_spend = min(1, subject.vp())
    max_vp_spend = max(max_vp_spend, subject.tvp())
    possible_vp_spends = [vp_spend for vp_spend in range(max_vp_spend + 1)]
    resource_spends = [spend for spend in itertools.product(possible_ap_spends, possible_vp_spends)]
    # calculate expected gains for different combinations of resources
    expected_kept = {}
    for (ap_spend, vp_spend) in resource_spends:
      expected_kept[(ap_spend, vp_spend)] = self.get_expected_kept_damage_dice(subject, target, skill, context, ap_spend, vp_spend)
    # climb resource expenditures for extra kept dice
    prev_kept = 2
    for vp_spend in range(max_vp_spend + 1):
      for ap_spend in range(max_ap_spend + 1):
        new_kept = expected_kept[(ap_spend, vp_spend)]
        if new_kept - prev_kept > 0:
          ap = ap_spend
          vp = vp_spend
          prev_kept = new_kept
        if new_kept == 6:
          # marginal benefit recedes after 6
          break
    if (ap > 0) or (vp > 0):
      margin = expected_kept[(ap, vp)] - expected_kept[(0, 0)] 
      logger.debug('{} spending {} VP (expecting to spend {} AP) to try to get {} extra kept damage dice'.format(subject.name(), vp, ap, margin))
    return self.get_attack_action(subject, target, skill, vp)

  def spend_action(self, character, skill, context):
    '''
    spend_action(character, skill, context) -> SpendActionEvent

    Spend an available action to take an attack.
    '''
    # spend the newest available action
    # older actions are usually more valuable
    chosen_phase = max([phase for phase in character.actions() if phase <= context.phase()])
    return events.SpendActionEvent(character, chosen_phase)
 
  def try_skill(self, character, skill, context):
    '''
    try_skill(character, skill, context) -> TakeAttackActionEvent or None

    Returns a TakeAttackActionEvent if the strategy can successfully
    find a target and optimize an attack using the given skill.
    '''
    if character.skill(skill) > 0:
      target = self.find_target(character, skill, context)
      if target is not None:
        attack = self.optimize_attack(character, target, skill, context)
        if attack is not None:
          logger.debug('{} is attacking {} with {}'.format(character.name(), target.name(), skill))
          return events.TakeAttackActionEvent(attack)

  def recommend(self, character, event, context):
    raise NotImplementedError()


class PlainAttackStrategy(BaseAttackStrategy):
  def recommend(self, character, event, context):
    if isinstance(event, events.YourMoveEvent):
      if character.has_action(context):
        target = self.find_target(character, 'attack', context)
        if target is not None:
          attack = self.optimize_attack(character, target, 'attack', context)
          logger.debug('{} is attacking {}'.format(character.name(), target.name()))
          yield self.spend_action(character, 'attack', context)
          yield events.TakeAttackActionEvent(attack)
        else:
          yield events.HoldActionEvent(character)
      else:
        yield events.NoActionEvent(character)


class UniversalAttackStrategy(BaseAttackStrategy):
  def recommend(self, character, event, context):
    if isinstance(event, events.YourMoveEvent):
      # TODO: implement intelligence around interrupts
      if character.has_action(context):
        # try to double attack first
        double_attack_event = self.try_skill(character, 'double attack', context)
        if double_attack_event is not None:
          yield self.spend_action(character, 'double attack', context)
          yield double_attack_event
          return
        # TODO: consider a lunge (probably need a LungeStrategy)
        if character.vp() == 0 and len(character.actions()) > 1:
          # if this character is out of VP and has more than one action in this round, a feint might be worth it
          feint_event = self.try_skill(character, 'feint', context)
          if feint_event is not None:
            yield self.spend_action(character, 'feint', context)
            yield feint_event
            return
        # try a plain attack
        attack_event = self.try_skill(character, 'attack', context)
        if attack_event is not None:
          yield self.spend_action(character, 'attack', context)
          yield attack_event
          return
        # fell through: do nothing
        yield events.HoldActionEvent(character)
      else:
        yield events.NoActionEvent(character)


class BaseParryStrategy(Strategy):
  def recommend(self, character, event, context):
    if isinstance(event, events.AttackRolledEvent):
      # bail if no action
      if not character.has_action(context) and not character.has_interrupt_action('parry', context):
        logger.debug('{} will not parry because no action'.format(character.name()))
        return
      # don't try to parry for enemies
      if event.action.target() not in character.group():
        logger.debug('{} will not parry for an enemy'.format(character.name()))
        return
      # don't try to parry a miss or an attack that is already parried
      if not event.action.is_hit():
        logger.debug('{} will not parry an attack that missed'.format(character.name()))
        return
      # don't try to parry an attack that is already parried
      if event.action.parried():
        logger.debug('{} will not parry an attack was already parried'.format(character.name()))
        return
      # delegate to specific parry strategy recommendation
      yield from self._recommend(character, event, context)

  def _recommend(self, character, event, context):
    raise NotImplementedError()

  def _can_shirk(self, character, event, context):
    '''
    Returns whether this character can shirk and let somebody else parry.
    '''
    # do my other friends have actions?
    others = character.group().friends_with_actions(context)
    for other_character in others:
      # can't pass the buck to myself
      if character != other_character:
        # did they already decline the parry?
        if other_character not in event.action.parries_declined():
          # are they willing to parry?
          if not isinstance(other_character.parry_strategy(), NeverParryStrategy):
            # shirk the parry
            return True
    return False

  def _estimate_damage(self, character, event, context):
    '''
    _estimate_damage(character, event, context) -> int

    Returns an estimate of how many SW this attack will inflict.
    '''
    # how much damage do we expect?
    expected_fire = TheoreticalCharacter(character.knowledge(), event.action.subject().name()).ring('fire')
    extra_dice = event.action.calculate_extra_damage_dice()
    weapon_rolled = event.action.subject().weapon().rolled()
    weapon_kept = event.action.subject().weapon().kept()
    expected_damage = context.mean_roll(expected_fire + weapon_rolled + extra_dice, weapon_kept)
    # how many wounds do we expect the target to take from this?
    target = event.action.target()
    (wc_rolled, wc_kept, wc_bonus) = target.get_wound_check_roll_params()
    expected_roll = context.mean_roll(wc_rolled, wc_kept) + wc_bonus
    expected_sw = target.wound_check(expected_roll, target.lw() + expected_damage)
    return expected_sw

  def spend_action(self, character, skill, context):
    '''
    spend_action(character, skill, context) -> SpendActionEvent

    Spend an available action to take an attack.
    '''
    # spend the newest available action
    # older actions are usually more valuable
    chosen_phase = max([phase for phase in character.actions() if phase <= context.phase()])
    yield events.SpendActionEvent(character, chosen_phase)
 

class AlwaysParryStrategy(BaseParryStrategy):
  '''
  Always parry for friends.
  '''
  def _recommend(self, character, event, context):
    logger.debug('{} always parries for friends'.format(character.name()))
    parry = actions.ParryAction(character, event.action.subject(), event.action)
    yield self.spend_action(character, 'parry', context)
    yield events.TakeParryActionEvent(parry)


class NeverParryStrategy(Strategy):
  '''
  Never parry.
  '''
  def recommend(self, character, event, context):
    logger.debug('{} never parries'.format(character.name()))
    yield from ()


class ReluctantParryStrategy(BaseParryStrategy):
  '''
  Parry if the hit is going to be bad and nobody else can parry.
  '''
  def _recommend(self, character, event, context):
    # let somebody else parry if possible
    # TODO: implement some kind of team parry strategy
    if self._can_shirk(character, event, context):
      logger.debug('{} is reluctant and shirks the parry'.format(character.name()))
      return
    # if parry was already attempted, no need to try again
    elif event.action.parry_attempted():
      logger.debug('{} is reluctant and will not parry when it was already attempted'.format(character.name()))
      return
    else:
      # how many wounds do we expect?
      expected_sw = self._estimate_damage(character, event, context)
      if event.action.skill() == 'double attack':
        expected_sw += 1
      # parry if it looks bad
      target = event.action.target()
      probably_fatal = target.sw_remaining() <= expected_sw
      probably_critical = expected_sw >= 2
      if probably_fatal or probably_critical:
        if probably_fatal:
          logger.debug('{} reluctantly parries because the attack would probably be fatal'.format(character.name()))
        elif probably_critical:
          logger.debug('{} reluctantly parries because the attack looks dangerous'.format(character.name()))
        parry = actions.ParryAction(character, event.action.subject(), event.action)
        yield self.spend_action(character, 'parry', context)
        yield events.TakeParryActionEvent(parry)
      else:
        logger.debug('{} will not parry a small attack'.format(character.name()))


class NeverParryStrategy(Strategy):
  def recommend(self, character, event, context):
    logger.debug('{} never parries'.format(character.name()))
    yield from ()


class SkillRolledStrategy(Strategy):
  '''
  Strategy to decide how to spend resources after a roll.
  '''
  def __init__(self):
    self._chosen_ap = 0
    self._chosen_bonuses = []

  def event_matches(self, character, event):
    '''
    Return whether this event is relevant for the strategy and character.
    '''
    raise NotImplementedError()

  def get_bonus_skills(self, event):
    '''
    Returns the skills that could be used for floating bonuses for
    this skill roll, in the order that they should be spent.

    For example, for a Double Attack, the character should spend
    floating bonuses for 'double attack' first, then 'attack_any',
    then 'any'.
    '''
    raise NotImplementedError()

  def get_tn(self, event):
    '''
    Return the desired TN.
    '''
    raise NotImplementedError()

  def recommend(self, character, event, context):
    if self.event_matches(character, event):
      self.reset()
      tn = self.get_tn(event)
      margin = tn - event.action.skill_roll()
      if margin <= 0:
        # if the roll was successful, do nothing
        yield event
        return
      # use floating bonuses to try to make the TN
      for skill in self.get_bonus_skills(event):
        self.use_floating_bonuses(character, skill, margin)
        margin = tn - event.action.skill_roll() - sum([t[1] for t in self._chosen_bonuses])
        if margin <= 0:
          break
      if margin > 0:
        # use adventure points to try to make the TN
        self.use_ap(character, event.action.skill(), margin)
        margin -= (5 * self._chosen_ap)
      if margin <= 0:
        # if we reached the TN, spend resources and update the event
        for (skill, bonus) in self._chosen_bonuses:
          yield events.SpendFloatingBonusEvent(character, skill, bonus)
        if self._chosen_ap > 0:
          yield events.SpendAdventurePointsEvent(character, skill, self._chosen_ap)
        new_roll = event.action.skill_roll() - sum([t[1] for t in self._chosen_bonuses]) - (5 * self._chosen_ap)
        event.action.set_skill_roll(new_roll)
        event.roll = new_roll
      yield event
    
  def reset(self):
    '''
    Reset this strategy. Should be called before each use.
    '''
    self._chosen_ap = 0
    self._chosen_bonuses.clear()

  def use_ap(self, character, skill, margin):
    if character.ap() > 0:
      if skill in character.ap_skills():
        ap_needed = math.ceil(margin / 5)
        max_spend = min(character.ap(), character.max_ap_per_roll())
        self._chosen_ap = min(max_spend, ap_needed)
       
  def use_floating_bonuses(self, character, skill, margin):
    available_bonuses = list(character.floating_bonuses(skill))
    available_bonuses.sort()
    while margin > 0 and len(available_bonuses) > 0:
      bonus = available_bonuses.pop(0)
      self._chosen_bonuses.append((skill, bonus))
      margin -= bonus


class AttackRolledStrategy(SkillRolledStrategy):
  def event_matches(self, character, event):
    return isinstance(event, events.AttackRolledEvent) and character == event.action.subject()

  def get_bonus_skills(self, event):
    return [event.action.skill(), 'attack_any', 'any']

  def get_tn(self, event):
    return event.action.tn()


class ParryRolledStrategy(SkillRolledStrategy):
  def event_matches(self, character, event):
    return isinstance(event, events.ParryRolledEvent) and character == event.action.subject()

  def get_bonus_skills(self, event):
    return [event.action.skill(), 'parry_any', 'any']

  def get_tn(self, event):
    return event.action.tn()


class WoundCheckRolledStrategy(SkillRolledStrategy):
  '''
  Strategy to decide how to spend resources to improve
  a wound check roll.

  This strategy is written to only spend resources to avoid
  defeat or taking more than 1 SW. It will not spend resources
  to try to succeed at the Wound Check.
  '''
  def __init__(self):
    self._chosen_ap = 0
    self._chosen_bonuses = []

  def recommend(self, character, event, context):
    if isinstance(event, events.WoundCheckRolledEvent):
      if event.subject == character:
        self.reset()
        # how many wounds would I take?
        expected_sw = character.wound_check(event.roll)
        if expected_sw == 0:
          # ignore it if no SW expected
          yield event
        else:
          # calculate how many SW are tolerable
          # normally 1 SW is tolerable
          # but if one wound means defeat, then only 0 SW is tolerable
          tolerable_sw = min(1, character.sw_remaining() - 1)
          # use wound check specific floating bonuses
          new_event = self.use_floating_bonuses(character, event, tolerable_sw, 'wound check')
          new_expected_sw = character.wound_check(new_event.roll)
          if new_expected_sw > tolerable_sw:
            # use universal floating bonuses
            new_event = self.use_floating_bonuses(character, new_event, tolerable_sw, 'any')
          new_expected_sw = character.wound_check(new_event.roll)
          if new_expected_sw > tolerable_sw:
            # use adventure points
            new_event = self.use_ap(character, new_event, tolerable_sw, 'wound check')
          new_expected_sw = character.wound_check(new_event.roll)
          # check if anything changed
          new_expected_sw = character.wound_check(new_event.roll)
          if new_expected_sw < expected_sw:
            # progress: spend resources and use the new roll
            for (skill, bonus) in self._chosen_bonuses:
              yield events.SpendFloatingBonusEvent(character, skill, bonus)
            yield events.SpendAdventurePointsEvent(character, self._chosen_ap)
            yield new_event
          else:
            # but the future refused to change
            # spend nothing and take the hit
            yield event

  def reset(self):
    self._chosen_ap = 0
    self._chosen_bonuses.clear()

  def use_ap(self, character, event, tolerable_sw, skill):
    ap = character.ap()
    max_spend = min(ap, character.max_ap_per_roll())
    new_roll = event.roll
    if character.can_spend_ap('wound check'):
      new_roll = event.roll
      new_expected_sw = character.wound_check(new_roll)
      while self._chosen_ap < max_spend:
        self._chosen_ap += 1
        new_roll += 5
        new_expected_sw = character.wound_check(new_roll)
        if new_expected_sw == tolerable_sw:
          break
    return events.WoundCheckRolledEvent(event.subject, event.attacker, event.damage, new_roll)

  def use_floating_bonuses(self, character, event, tolerable_sw, skill):
    available_bonuses = character.floating_bonuses(skill)
    available_bonuses.sort()
    new_roll = event.roll
    new_expected_sw = character.wound_check(new_roll)
    for bonus in available_bonuses:
      self._chosen_bonuses.append((skill, bonus))
      new_roll += bonus
      new_expected_sw = character.wound_check(new_roll)
      if new_expected_sw == tolerable_sw:
        break
    return events.WoundCheckRolledEvent(event.subject, event.attacker, event.damage, new_roll) 


class KeepLightWoundsStrategy(Strategy):
  '''
  Strategy to decide whether to keep LW or take SW.
  '''
  def recommend(self, character, event, context):
    if isinstance(event, events.WoundCheckSucceededEvent):
      if event.subject == character:
        if event.damage > event.roll:
          raise RuntimeError('KeepLightWoundsStrategy should not be consulted for a failed wound check')
        # keep LW to avoid unconsciousness
        if character.sw_remaining() == 1:
          logger.debug('{} keeping light wounds to avoid defeat.'.format(character.name()))
          return
        # how much damage do we expect to take in the future?
        expected_damage = 0
        if len(character.lw_history()) == 0:
          expected_damage = context.mean_roll(7, 2)
        else:
          expected_damage = int(sum(character.lw_history()) / len(character.lw_history()))
        # what do we expect to get for the next wound check?
        (rolled, kept, modifier) = character.get_wound_check_roll_params()
        future_damage = character.lw() + expected_damage
        expected_roll = context.mean_roll(rolled, kept) + modifier
        # how many wounds do we expect?
        if character.wound_check(expected_roll, future_damage) > 2:
          # take the wound if the next wound check probably will be bad
          logger.debug('{} taking a serious wound because the next wound check might be bad.'.format(character.name()))
          yield events.TakeSeriousWoundEvent(character, event.attacker, 1)
        else:
          logger.debug('{} keeping light wounds because the next wound check should be ok.'.format(character.name()))


class WoundCheckStrategy(Strategy):
  '''
  Strategy to decide how many VP to spend on a wound check.
  '''
  def recommend(self, character, event, context):
    if isinstance(event, events.LightWoundsDamageEvent):
      if event.target == character:
        spend_vp = 0
        declared_vp = self._declare_vp(character, event, context)
        yield events.WoundCheckDeclaredEvent(character, event.subject, event.damage, declared_vp)

  def _declare_vp(self, character, event, context):
    # get roll params
    (rolled, kept, modifier) = character.get_wound_check_roll_params()
    # initialize climbing parameters
    declared_vp = 0
    planned_ap = 0
    max_vp = min(character.max_vp_per_roll(), character.vp())
    max_ap = min(character.max_ap_per_roll(), character.ap())
    new_rolled = rolled
    new_kept = kept
    new_modifier = modifier
    # how many SW are expected?
    # TODO: be more conservative and calculate the worst roll within 1 stdev of the mean
    expected_roll = context.mean_roll(rolled, kept) + modifier
    expected_sw = character.wound_check(expected_roll)
    # tolerable_sw is normally 1
    # but if 1 SW from defeat, tolerable SW is 0
    tolerable_sw = min(character.sw_remaining() - 1, 1)
    while expected_sw > tolerable_sw:
      if declared_vp == max_vp:
        # stop trying to spend VP if maxed out
        break
      elif new_kept == 10:
        # stop trying to spend VP if already keeping 10 dice
        break
      declared_vp += 1
      if planned_ap < (2 * declared_vp) and planned_ap < max_ap:
        # try to spend 2 AP per VP
        planned_ap += min(2, max_ap - planned_ap)
      (new_rolled, new_kept, modifier) = normalize_roll_params(
        new_rolled + declared_vp,
        new_kept + declared_vp,
        new_modifier)
      expected_roll = context.mean_roll(new_rolled, new_kept) \
        + new_modifier + (5 * planned_ap)
      expected_sw = character.wound_check(expected_roll)
    logger.debug('{} declaring {} VP for wound check'.format(character.name(), declared_vp))
    return declared_vp
    
