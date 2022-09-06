from l7r.combatant import Combatant


def create_r5t_trigger(defender, enemy):
    def trigger(check, light, light_total):
        exceeded = max(0, check - light)
        if exceeded:
            enemy.tn -= exceeded
            enemy.events['post_defense'].append(enemy.reset_tn)
    return trigger


def create_r5t_reset(defender, func):
    def trigger():
        self.events['wound_check'].remove(func)
    return trigger


class DaidojiBushi(Combatant):
    school_knacks = ['counterattack', 'double_attack', 'iaijutsu']
    r1t_rolls = ['attack', 'counterattack', 'wound_check']
    r2t_rolls = 'counterattack'

    def __init__(self, **kwargs):
        Combatant.__init__(self, **kwargs)
        self.events['pre_attack'].append(self.r3t_trigger)
        self.events['pre_attack'].append(self.r5t_trigger)

    def r3t_trigger(self):
        if self.rank >= 3 and self.attack_knack == 'counterattack':
            self.countering_for.always['wound_check'] += 4 * self.attack

            def reset_wc():
                self.countering_for.always['wound_check'] -= 4 * self.attack
                return True
            self.countering_for.events['post_defense'].append(reset_wc)

    def r5t_trigger(self):
        if self.rank == 5 and self.attack_knack == 'counterattack':
            trigger = create_r5t_trigger(self.countering_for, self.enemy)
            self.countering_for.events['wound_check'].append(trigger)
            self.countering_for.events['post_defense'].append(create_r5t_reset(self.countering_for))

    def will_counterattack(self, enemy):
        pass

    def will_counterattack_for(self, ally, enemy):
        pass
