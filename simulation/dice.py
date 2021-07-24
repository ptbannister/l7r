from __future__ import division
from common import *

try:
    from probabilities import prob
    for reroll in [True, False]:
        d = defaultdict(int)
        d.update(prob[reroll])
        prob[reroll] = d
except:
    pass

def avg(reroll, roll, keep):
    return prob[reroll][roll, keep] or (41 + roll + keep)

def d10(reroll=True):
    total = die = randrange(1, 11)
    while reroll and die==10:
        die = randrange(1, 11)
        total += die
    return total

def actual_xky(roll, keep):
    bonus = 0
    if roll > 10:
        keep += roll - 10
        roll = 10
    if keep > 10:
        bonus = keep - 10
        keep = 10
    
    return roll, keep, bonus

def xky(roll, keep, reroll=True):
    roll, keep, bonus = actual_xky(roll, keep)
    return bonus + sum(sorted(d10(reroll) for i in range(roll))[-keep:])

if __name__ == "__main__":
    [fname] = sys.argv[1:2] or ["probabilities.py"]
    ROLLS = 1000
    prob = {True: defaultdict(int), False: defaultdict(int)}
    for i in range(ROLLS):
        for rolled in range(1, 11):
            for kept in range(1, rolled+1):
                for reroll in [True, False]:
                    result = xky(rolled, kept, reroll)
                    prob[reroll][rolled,kept] += result
                    for tn in range(result):
                        prob[reroll][rolled,kept,tn] += 1
                    
                    if rolled == 10:
                        for j in range(kept-1, 1, -1):
                            prob[reroll][rolled + j, kept - j] += result
                            for tn in range(result):
                                prob[reroll][rolled + j, kept - j, tn] += 1
    
    for reroll in [True, False]:
        prob[reroll]  = dict((key, val/ROLLS) for key,val in prob[reroll].items())
    
    with open(fname, "w") as f:
        f.write("prob = ")
        pprint(prob, stream=f)
