
from abc import ABC, abstractmethod

from simulation.actions import AttackAction, ParryAction
from simulation.events import AttackDeclaredEvent, AttackRolledEvent, LightWoundsDamageEvent, NewPhaseEvent, TakeAttackActionEvent, TakeParryActionEvent, TakeSeriousWoundEvent, WoundCheckDeclaredEvent, WoundCheckRolledEvent, WoundCheckSucceededEvent
from simulation.log import logger

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
    if not isinstance(event, NewPhaseEvent):
      return None
    # try to attack if action available
    # TODO:
    if character.has_action(context):
      return character.attack_strategy().recommend(character, event, context)
    # TODO: evaluate whether to interrupt
    return None


class AttackStrategy(Strategy):
  def recommend(self, character, event, context):
    if isinstance(event, NewPhaseEvent):
      if character.has_action(context):
        # TODO: implement intelligence around interrupts
        target = self._find_target(character, context)
        if target is not None: 
          attack = AttackAction(character, target)
          # TODO: attempt to hit and get extra kept damage dice by spending AP and VP
          logger.debug('{} is attacking {}'.format(character.name(), target.name()))
          return TakeAttackActionEvent(attack)
    # do nothing
    return None

  def _find_target(self, character, context):
    targets = []
    for other_character in context.characters():
      # don't try to fight yourself or your buddies
      if other_character not in character.group():
        # don't stab the corpses
        if other_character.is_fighting():
          # can I hit this character?
          tn_to_hit = character.knowledge().tn_to_hit(other_character)
          # TODO: figure out what ring and skill to use
          (rolled, kept, bonus) = character.get_skill_roll_params('fire', 'attack')
          # TODO: prefer certain targets because they are closer to defeat, or they are more dangerous, etc
          p_hit = context.p(tn_to_hit - bonus, rolled, kept)
          targets.append((other_character, p_hit))
    # sort targets in order of probability of hitting
    targets.sort(key=lambda t: t[1], reverse=True)
    # return the easiest target to hit
    if len(targets) > 0:
      return targets[0][0]
    else:
      return None


class BaseParryStrategy(Strategy):
  def recommend(self, character, event, context):
    if isinstance(event, AttackRolledEvent):
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
      return self._recommend(character, event, context)

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
    extra_dice = event.action.calculate_extra_damage_dice()
    expected_damage = context.mean_roll(7 + extra_dice, 2)
    # how many wounds do we expect the target to take from this?
    target = event.action.target()
    (wc_rolled, wc_kept, wc_bonus) = target.wound_check_params()
    expected_roll = context.mean_roll(wc_rolled, wc_kept) + wc_bonus
    expected_sw = target.wound_check(expected_roll, target.lw() + expected_damage)
    return expected_sw


class AlwaysParryStrategy(BaseParryStrategy):
  '''
  Always parry for friends.
  '''
  def _recommend(self, character, event, context):
    logger.debug('{} always parries for friends'.format(character.name()))
    parry = ParryAction(character, event.action.subject(), event.action)
    return TakeParryActionEvent(parry)


class NeverParryStrategy(Strategy):
  '''
  Never parry.
  '''
  def recommend(self, character, event, context):
    logger.debug('{} never parries'.format(character.name()))


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
        parry = ParryAction(character, event.action.subject(), event.action)
        return TakeParryActionEvent(parry)
      else:
        logger.debug('{} will not parry a small attack'.format(character.name()))


class NeverParryStrategy(Strategy):
  def recommend(self, character, event, context):
    logger.debug('{} never parries'.format(character.name()))


class KeepLightWoundsStrategy(Strategy):
  '''
  Strategy to decide whether to keep LW or take SW.
  '''
  def recommend(self, character, event, context):
    if isinstance(event, WoundCheckSucceededEvent):
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
        # what is the probability of making the next wound check?
        (rolled, kept, bonus) = character.get_wound_check_roll_params()
        future_damage = character.lw() + expected_damage
        p_fail_by_ten = 1.0 - context.p(future_damage - bonus - 10, rolled, kept)
        if p_fail_by_ten > 0.5:
          # take the wound if the next wound check probably will be bad
          logger.debug('{} taking a serious wound because the next wound check might be bad.'.format(character.name()))
          return TakeSeriousWoundEvent(character, 1)
        else:
          logger.debug('{} keeping light wounds because the next wound check should be ok.'.format(character.name()))


class WoundCheckStrategy(Strategy):
  '''
  Strategy to decide how many VP to spend on a wound check.
  '''
  def recommend(self, character, event, context):
    if isinstance(event, LightWoundsDamageEvent):
      if event.target == character:
        (rolled, kept, bonus) = character.get_wound_check_roll_params()
        spend_vp = 0
        # What is the probability of making the roll?
        p_success = context.p(event.damage - bonus, rolled, kept)
        if p_success < 0.5:
          # What is the probability of failing by 10 or more?
          p_fail_bad = context.p(event.damage - bonus - 10, rolled, kept)
         
        return WoundCheckDeclaredEvent(character, event.damage, 0)

