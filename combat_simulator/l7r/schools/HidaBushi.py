from l7r.combatant import Combatant


class HidaBushi(Combatant):
    school_knacks = ['counterattack', 'double_attack', 'iaijutsu']
    r1t_rolls = ['attack', 'counterattack', 'wound_check']
    r2t_rolls = 'counterattack'

    def __init__(self, **kwargs):
        Combatant.__init__(self, **kwargs)
        self.events['successful_attack'].append(self.r5t_succ_trigger)

    def r5t_succ_trigger(self):
        if self.rank == 5 and self.attack_knack == 'counterattack':
            exceeded = max(0, self.attack_roll - enemy.tn)
            if exceeded:
                self.always['wound_check'] += exceeded

                def reset_wc():
                    self.always['wound_check'] -= exceeded
                    return True
                self.events['post_defense'].append(reset_wc)

    def xky(self, roll, keep, reroll, roll_type):
        if self.rank >= 3 and roll_type == 'counterattack':
            dice = sorted(d10(reroll) for i in range(roll))
            remaining = 2 * self.attack
            while remaining:
                retries = min(remaining, 10 - keep)
                dice[:retries] = [d10(reroll) for i in range(retries)]
                dice.sort()
                remaining -= retries
            return sum(dice[-keep:])

        return Combatant.xky(self, roll, keep, reroll, roll_type)

    def wound_check(self, light, serious=0):
        if self.rank == 5 and self.actions and self.avg_serious(light, *self.wc_dice) > 1:
            if self.actions[0] <= self.phase:
                self.actions.pop(0)
            else:
                self.actions.pop()
                self.tn -= 5
                self.events['post_defense'].append(self.reset_tn)
            self.engine.attack('counterattack', self, self.enemy)

        prev_serious = self.serious
        Combatant.wound_check(self, light, serious)
        if self.rank >= 4 and self.serious > (serious + prev_serious + 2) and self.vps:
            self.vps -= 1
            self.serious = serious + prev_serious + 2

    def will_counterattack(self, enemy):
        pass

    def will_counterattack_for(self, ally, enemy):
        pass

    def choose_action(self):
        pass
