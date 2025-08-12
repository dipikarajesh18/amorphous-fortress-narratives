# "[@.b1ea] pushed [*.e209]"
# "[*.e209] transformed into [O.42f5] at 4,6"

import random
import datetime
POS_RANGE = (0, 99)


def randomEnt():
    ''' Generates a new entity ID '''
    s = random.choice([chr(a) for a in range(32, 127)])
    id = ''.join(random.choices('0123456789abcdef', k=4))
    return f"{s}.{id}"


def sameEnt(symbol):
    id = ''.join(random.choices('0123456789abcdef', k=4))
    return f"{symbol}.{id}"


def randomPos():
    x = random.choice(list(range(POS_RANGE[0], POS_RANGE[1])))
    y = random.choice(list(range(POS_RANGE[0], POS_RANGE[1])))
    return (x,y)


def adjPos(p):
    dir = random.choice([[0,1],[0,-1],[1,0],[-1,0]])
    np = (p[0]+dir[0], p[1]+dir[1])
    return np


def randomLog(ents):
    ''' Makes a new logged item
        Key: E -- entity (symbol.id),  N -- same entity (synbol.new id), O -- other entity, 
                P - position (x,y), Q -- other position
    '''
    log_set = [
        "[E_] moved to (P_)",
        "[E_] moved to (P_)",
        "[E_] moved to (P_)",
        "[E_] moved to (P_)",
        "[E_] moved to (P_)",       # 5x likely to move
        "[E_] died",
        "[E_] cloned to [N_] at (Q_)",
        "[E_] took [O_]",
        "[E_] moved to (P_) [target: (Q_)]",
        "[E_] pushed [O_]",
        "[E_] added [O_] at (Q_)",
        "[E_] transformed into [O_] at (P_)",
        "[E_] blocked by wall [O_]"
    ]

    l = random.choice(log_set)

    random.shuffle(ents)

    e = ents[0]
    o = ents[1]
    n = sameEnt(e[0])
    p = randomPos()
    q = str(adjPos(p))
    p = str(p)

    l = l.replace('E_', e)
    l = l.replace('O_', o)
    l = l.replace('(P_)', p)
    l = l.replace('N_', n)
    l = l.replace('(Q_)', q)

    return l


if __name__ == "__main__":
    random.seed = random.randint(100000, 999999)
    ents = [randomEnt() for _ in range(20)]

    fake_log = []
    d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fake_log = [f"=====    FORTRESS SEED: [{random.seed}]    =====", "Fortress initialized! - <0>", f">>> TIME: {d} <<<"]
    #print(ents)

    for i in range(10):
        if random.random() > 0.2:
            fake_log.append(f"<{i}> {randomLog(ents)}")
        if random.random() > 0.9:           # chance of double log
            fake_log.append(f"<{i}> {randomLog(ents)}")

    print("\n".join(fake_log))

    with open("stupid_log.txt", "w+") as f:
        f.write("\n".join(fake_log))

