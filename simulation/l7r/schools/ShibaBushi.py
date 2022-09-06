from l7r.combatant import Combatant


class ShibaBushi(Combatant):
    school_knacks = ['double_attack', 'counterattack', 'iaijutsu']
    r1t_rolls = ['counterattack', 'double_attack', 'parry']
    r2t_rolls = 'parry'

    def __init__(self, **kwargs):
        Combatant.__init__(self, **kwargs)

        self.events['successful_parry'].append(self.r3t_trigger)
        self.events['successful_parry'].append(self.r5t_trigger)

    def r3t_trigger(self):
        if self.rank >= 3:
            damage = self.xky(2 * self.attack, 1, True, 'damage')
            self.log(f'deals {damage} damage with R3T')
            enemy.wound_check(damage, 0)

    def r5t_trigger(self):
        exceeded = max(0, self.parry_roll - self.enemy.attack_roll)
        if exceeded and self.rank == 5:
            old_tn = self.enemy.tn
            self.enemy.tn = max(0, self.enemy.tn - exceeded)

            def restore():
                self.enemy.tn = old_tn
                return True
            enemy.events['post_attack'].append(restore)

    def choose_action(self):
        pass

    def make_parry_for(self, ally, enemy):
        return self.make_parry(enemy)

    def will_predeclare(self):
        pass

    def will_predeclare_for(self, ally, enemy):
        pass

    def will_parry(self):
        pass

    def will_parry_for(self, ally, enemy):
        pass
