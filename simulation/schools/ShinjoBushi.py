from common import *

class ShinjoBushi(Combatant):
    school_knacks = ["double_attack", "iaijutsu", "lunge"]
    r1t_rolls = ["double_attack", "parry", "wound_check"]
    r2t_rolls = "parry"
    
    def __init__(self, **kwargs):
        Combatant.__init__(self, **kwargs)
        
        self.events["successful_parry"].append(self.r3t_trigger)
        self.events["successful_parry"].append(self.r5t_trigger)
    
    def r3t_trigger(self):
        if self.rank >= 3:
            for i in range(len(self.actions)):
                self.actions[i] -= self.attack
    
    def r5t_trigger(self):
        exceeded = max(0, self.parry_roll - self.enemy.attack_roll)
        if exceeded and self.rank == 5:
            self.disc["wound_check"].append(exceeded)
    
    @property
    def wc_threshold(self):
        return max(self.base_wc_threshold, self.max_bonus("wound_check"))
    
    def initiative(self):
        Combatant.initiative(self)
        if self.rank >= 4:
            self.actions.insert(0, 1)
            highest = self.actions.pop()
            self.init_order = self.actions[:]
            self.log("R4T sets highest action die ({0}) to 1", highest)
    
    def choose_action(self):
        if self.actions and self.actions[0] <= self.phase:
            bonus = 2 * (self.phase - self.actions[0])
            
            
