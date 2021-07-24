from common import *

class KuniWitchHunter(Combatant):
    school_knacks = ["detect_taint", "iaijutsu", "presence"]
    r1t_rolls = ["interrogation", "attack", "wound_check"]
    r2t_rolls = "interrogation"
    
    def __init__(self, **kwargs):
        Combatant.__init__(self, **kwargs)
        
        if self.rank >= 3:
            self.disc["wound_check"].extend([5] * self.attack)
    
    @property
    def wc_dice(self):
        roll, keep = super(KuniWitchHunter, self).wc_dice
        return roll+1, keep+1
    
    def initiative(self):
        Combatant.initiative(self)
        self.extra_parry = self.rank >= 4
    
    def wound_check(self, light, serious=0):
        Combatant.wound_check(self, light, serious)
        if self.rank == 5 and WHEN_DO_WE_USE_THIS:
            Combatant.wound_check(self, light, serious)
            self.enemy.wound_check(light)
    
    def will_parry(self):
        pass
    
    def will_parry_for(self, ally, enemy):
        pass
