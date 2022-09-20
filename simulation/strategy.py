
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
    if character.has_action():
      if context.phase() >= min(character.actions()):
        return character.attack_strategy().recommend(character, event, context)
    # TODO: evaluate whether to interrupt
    return None


class AttackStrategy(Strategy):
  def recommend(self, character, event, context):
    if isinstance(event, NewPhaseEvent):
      if character.has_action():
        # TODO: implement intelligence around interrupts
        if context.phase() >= min(character.actions()):
          target = self.find_target(character, context)
          if target is not None: 
            attack = AttackAction(character, target)
            # TODO: figure out how to decide to spend VP
            return TakeAttackActionEvent(attack)
    # do nothing
    return None

  def find_target(self, character, context):
    # TODO: implement better targeting algorithm
    for other_character in context.characters():
      if other_character != character:
        if other_character.is_fighting():
          return other_character
    return None


class ParryStrategy(Strategy):
  def recommend(self, character, event, context):
    if isinstance(event, AttackRolledEvent):
      # is this character in my group?
      if event.action.target().group() == character.group():
        # did it hit?
        if event.action.is_hit() and not event.action.parried():
          # TODO: calculate whether I might lose from this attack
          too_perilous = False
          # was it a big hit?
          extra_dice = event.action.calculate_extra_damage_dice()
          if extra_dice >= 4 or event.action.skill() == 'double attack' or too_perilous:
            # do I have an action?
            # TODO: handle ability to interrupt
            if context.phase() >= min(character.actions()):
              parry = ParryAction(character, event.action.subject(), event.action)
              return TakeParryActionEvent(parry)
            else:
              logger.debug('{} cannot parry, no action in current phase.'.format(character.name()))
          else:
            logger.debug('{} will not parry a small attack.'.format(character.name()))
        else:
          logger.debug('{} will not parry because attack missed or is already parried.'.format(character.name()))
      else:
        logger.debug('{} will not parry because target is not an ally.'.format(character.name()))


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
        (rolled, kept, bonus) = character.get_wound_check_roll_parameters()
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
        (rolled, kept, bonus) = character.get_wound_check_roll_parameters()
        spend_vp = 0
        # What is the probability of making the roll?
        p_success = context.p(event.damage - bonus, rolled, kept)
        if p_success < 0.5:
          # What is the probability of failing by 10 or more?
          p_fail_bad = context.p(event.damage - bonus - 10, rolled, kept)
         
        return WoundCheckDeclaredEvent(character, event.damage, 0)

