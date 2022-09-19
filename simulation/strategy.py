
from abc import ABC, abstractmethod

from simulation.actions import AttackAction
from simulation.events import AttackDeclaredEvent, LightWoundsDamageEvent, NewPhaseEvent, TakeAttackActionEvent, TakeSeriousWoundEvent, WoundCheckDeclaredEvent, WoundCheckRolledEvent, WoundCheckSucceededEvent

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
      if context.phase() == min(character.actions()):
        return character.attack_strategy().recommend(character, event, context)
    # TODO: evaluate whether to interrupt
    return None


class AttackStrategy(Strategy):
  def recommend(self, character, event, context):
    if isinstance(event, NewPhaseEvent):
      if character.has_action():
        # TODO: implement intelligence around interrupts
        if context.phase() == min(character.actions()):
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
    # TODO: handle AttackDeclared and determine whether to parry
    # TODO: handle AttackPredeclared and determine whether to parry
    return None


class KeepLightWoundsStrategy(Strategy):
  '''
  Strategy to decide whether to keep LW or take SW.
  '''
  def recommend(self, character, event, context):
    if isinstance(event, WoundCheckSucceededEvent):
      if event.subject == character:
        if event.damage > event.roll:
          raise RuntimeError('KeepLightWoundsStrategy should not be consulted for a failed wound check')
        # TODO: attempt to keep LW if likely to pass future wound checks
        return TakeSeriousWoundEvent(character, 1)


class WoundCheckStrategy(Strategy):
  '''
  Strategy to decide how many VP to spend on a wound check.
  '''
  def recommend(self, character, event, context):
    if isinstance(event, LightWoundsDamageEvent):
      if event.target == character:
        # TODO: calculate expected outcome and spend VP appropriately
        return WoundCheckDeclaredEvent(character, event.amount, 0)

