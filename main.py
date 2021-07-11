from SVEncodeDecode import encode_SV
from SVEncodeDecode import SV
from bpmlinehelper import GhostLines
from math import exp, sin, floor, pi, cos
from random import random

def DecodeToFile(osufile, newfilename, SVLines: list):
    with open(newfilename, "w+") as f:
        old = open(osufile, "r")
        old = old.readlines()
        old_TotimingPoints = old[:old.index("[TimingPoints]\n") + 1]
        old_afterTimingPoints = old[old.index("[TimingPoints]\n") + 1:]
        all_file = old_TotimingPoints + [i.encode() for i in SVLines] + old_afterTimingPoints
        for k in all_file:
            f.write(k)

def Noteoffset(osufile, start, end, return_only_LN=False):
    with open(osufile, 'r') as f:
        f = f.readlines()
        offseto = []
        notecount = []
        for i in range(f.index("[HitObjects]\n")+1, len(f) - 1):
            if start <= int(f[i].split(",")[2]) <= end:
                if int(f[i].split(",")[2]) in offseto:
                    notecount[-1] += 1
                    continue
                if return_only_LN:
                    splited = f[i].split(",")
                    release = int(splited[-1].split(":")[0])
                    if release == 0:
                        continue
                    else:
                        offseto.append([int(splited[2]), release])
                else:
                    offseto.append(int(f[i].split(",")[2]))
                    notecount.append(1)
    return offseto, notecount

def noteColumn(osufile, start, end):
    with open(osufile, 'r') as f:
        f = f.readlines()
        offseto = []
        columns = []
        for i in range(f.index("[HitObjects]\n")+1, len(f) - 1):
            if start <= int(f[i].split(",")[2]) <= end:
                if int(f[i].split(",")[2]) in offseto:
                    columns[-1].append(int(f[i].split(",")[0]) // 128)
                    continue
                offseto.append(int(f[i].split(",")[2]))
                columns.append([int(f[i].split(",")[0]) // 128])
    return offseto, columns
NSVFile = "II-L - EXPLORER-2 (HowToPlayLN) [tetralriddim].osu"
bpm = 340

def get_snap(bpm, snap):
    return 60000 / bpm * snap

REDLINES = True

def intro(start, end):
    # sudden teleport and then funny bpm lines
    svs = []
    offsets, notecount = Noteoffset(NSVFile, start, end)
    del notecount
    for ofs1, ofs2 in zip(offsets[:-1], offsets[1:]):
        # sudden teleport
        sv_set = []
        if REDLINES:
            sv_set.append(SV(ofs1, 1000000, 20, 1))
        else:
            sv_set.append(SV(ofs1, 10, 20, 0))
        # Funny bpm lines
        i = ofs1
        x = 1
        while i + get_snap(bpm, 1/8) < ofs2:
            next_snap = get_snap(bpm, 1/8)
            if REDLINES:
                sv_set.append(SV(i + next_snap, 100000 / x, 20, 1))
                sv_set.append(SV(i + next_snap, 0.01, 20, 0))
            else:
                sv_set.append(SV(i + next_snap, 10 / x, 20, 0))
            i += next_snap
            x += 1
        
        svs += sv_set.copy()
    if REDLINES:
        svs.append(SV(ofs2, bpm, 20, 1))
    else:
        svs.append(SV(ofs2, 1, 20, 0))
    return svs
        
def buildup_0(start, end):
    # e^-(kx) slowjam and accerlate every 2 notes
    # and then sum up shit

    k = 0.004

    def singleExponentialSlowJam(offset):
        return lambda x: exp(-k * (x - offset)) if x >= offset else 0
    
    def exponentialSlowJam(offsets):
        def f(x):
            funcs = [singleExponentialSlowJam(ofs) for ofs in offsets]
            res = 0
            for func in funcs:
                res += func(x)
            return res
        return f
    
    ofs, notecount = Noteoffset(NSVFile, start, end)
    f = exponentialSlowJam(list(filter(lambda x: notecount[ofs.index(x)] == 2, ofs)))
    i = start
    svs = []
    while i < end:
        if REDLINES:
            svs.append(SV(i, f(i) * bpm, 20, 1))
        # Green lines
        else:
            svs.append(SV(i, f(i), 20, 0))
        i += get_snap(bpm, 1/8)
    return svs

def main_1(start, end):
    section = []
    ofs, notecount = Noteoffset(NSVFile, start, end)
    del notecount
    # sinewave but its not really sine wave
    for o, o2 in zip(ofs[:-1], ofs[1:]):
        section.append(SV(o - 1, sin((o - start) / 1000) * 60000 + 60000.001, 20, 1))
        section.append(SV(o, 1000000, 20, 1))
        section.append(SV(o + 1, abs((sin((o2 - start) / 1000) - sin((o - start) / 1000))) * 60000 / (o2 - o) + 0.001, 20, 1))
    return section

def main_stac(start, end):
    v = []
    offsets, _ = Noteoffset(NSVFile, start, end)
    del _
    def f(t):
        T = (t - start) / (get_snap(bpm, 1) * 10)
        if floor(T) % 2 == 0:
            return abs(T - floor(T) - 0.5001) * 0.5
        else:
            return (1 - abs(T - floor(T) - 0.5001)) * 0.5
        
    def get_5_hitobjects(t):
        n = list(filter(lambda x: t < x < t + (get_snap(bpm, 1) * 10), offsets))
        return n
    temp = start
    while temp < end:
        svlines = [f(temp)]
        for i in get_5_hitobjects(temp):
            svlines.append(f(i))
        lines = GhostLines(svlines).get_SV(temp) + [SV(temp + 3, 0.001, 20, 1)]
        v += lines
        temp += get_snap(bpm, 1/8)
    return v

def main_stac_melo(start, end):
    section = []
    offsets, notecount = Noteoffset(NSVFile, start, end)
    offsets_only_doubles = list(filter(lambda i: notecount[offsets.index(i)] == 2, offsets))
    prev = 0
    next_ = 1
    def f(t):
        return 0.5 - 0.5 * (t - offsets_only_doubles[prev]) / (offsets_only_doubles[next_] - offsets_only_doubles[prev])
    def get_hit_between():
        return list(filter(lambda x: t < x < offsets_only_doubles[next_], offsets))
    t = start
    while t < end:
        temp = []
        if offsets_only_doubles[prev] <= t <= offsets_only_doubles[next_]:
            temp.append(f(t))
            temp += [f(i) for i in get_hit_between()]
            t += get_snap(bpm, 1/8)
            lines = GhostLines(temp).get_SV(t) + [SV(t + 3, 0.001, 20, 1)]
            section += lines
        else:
            prev += 1
            next_ += 1
    return section

def buildup_1(start, end):
    # same concept as buildup_0 w/ fancier stuff
    section = []
    k = 0.004

    def singleExponentialSlowJam(offset):
        return lambda x: exp(-k * (x - offset)) if x >= offset else 0.001
    
    def exponentialSlowJam(offsets):
        def f(x):
            funcs = [singleExponentialSlowJam(ofs) for ofs in offsets]
            res = 0
            for func in funcs:
                res += func(x)
            return res * 100000
        return f
    
    def differentialExponentialSlowJam(offsets):
        def f(x):
            funcs = [singleExponentialSlowJam(ofs) for ofs in offsets]
            res = 0
            for func in funcs:
                d = k * func(x)
                res += d
            return res * 100000
        return f
    

    # lemme think how to do it
    ofs, notecount = Noteoffset(NSVFile, start, end)
    f = exponentialSlowJam(list(filter(lambda x: notecount[ofs.index(x)] == 2, ofs)))
    df = differentialExponentialSlowJam(list(filter(lambda x: notecount[ofs.index(x)] == 2, ofs)))

    for o1, o2 in zip(ofs[:-1], ofs[1:]):
        section.append(SV(o1 - 1, f(o1), 20, 1))
        section.append(SV(o1, 1000000, 20, 1))
        i = o1 + 1
        while i < o2:
            section.append(SV(i, df(i), 20, 1))
            i += get_snap(bpm, 1/8)
    return section

def even_drum_section1(start, end):
    drums = get_snap(bpm, 2)
    v = []
    offsets, _ = Noteoffset(NSVFile, start, end)
    del _
    def f(t):
        T = (t - start) / (get_snap(bpm, 1) * 5)
        if floor(T) % 2 == 0:
            return abs(T - floor(T) - 0.5001) * 0.5
        else:
            return (1 - abs(T - floor(T) - 0.5001)) * 0.5
        
    def get_5_hitobjects(t):
        n = list(filter(lambda x: t < x < t + (get_snap(bpm, 1) * 5), offsets))
        return n
    temp = start
    while temp < end:
        if (temp - start) % drums >= 50:
            svlines = [f(temp)]
            for i in get_5_hitobjects(temp):
                svlines.append(f(i))
            lines = GhostLines(svlines).get_SV(temp) + [SV(temp + 3, 340, 20, 1), SV(temp + 3, 0.01, 20, 1)]
            v += lines
            temp += get_snap(bpm, 1/8)
        else:
            svlines = [i / 50 for i in range(1, 50)]
            lines = GhostLines(svlines).get_SV(temp) + [SV(temp + 3, 340, 20, 1), SV(temp + 3, 0.01, 20, 1)]
            v += lines
            temp += get_snap(bpm, 1/8)
    return v

def even_drum_section2(start, end):
    drums = get_snap(bpm, 2)
    v = []
    def sinewave_bottom(x):
        return (cos((x - start) / drums * pi) ** 2)
    
    t = start
    offsets, columns = noteColumn(NSVFile, start, end)
    i = 0
    while t < end:
        svlines = [sinewave_bottom(t) * 0.04 * k for k in range(1, 6)]
        if offsets[i] < t:
            i += 1
        else:
            top = [0.2, 0.4, 0.6, 0.8, 1]
            for c in columns[i]:
                a = c * 0.2 + 0.2
                top += [a, a + 0.05, a + 0.1, a + 0.15]
            svlines += top
            lines = GhostLines([x * 0.6 for x in svlines]).get_SV(t) + [SV(t + 3, 340, 20, 1), SV(t + 3, 0.01, 20, 1)]
            v += lines
            t += get_snap(bpm, 1/8)
    return v

def even_drum_section3(start, end):
    drums = get_snap(bpm, 2)
    v = []
    temp = start
    offsets, columns = noteColumn(NSVFile, start, end)
    def f(t):
        def m(t, i):
            if 0 < offsets[i] - t < get_snap(bpm, 2):
                return [(c + 1) * 0.25 - 0.25 / get_snap(bpm, 2) * (get_snap(bpm, 2) + t - offsets[i]) for c in columns[i]]
            return []
        res = []
        for i in range(len(offsets)):
            res += m(t, i)
        return res
    while temp < end:
        if (temp - start) % drums >= 25:
            svlines = f(temp) + [0.25, 0.5, 0.75, 1]
            lines = GhostLines([i * 0.5 for i in svlines]).get_SV(temp) + [SV(temp + 3, 340, 20, 1), SV(temp + 3, 0.01, 20, 1)]
            v += lines
            temp += get_snap(bpm, 1/8)
        else:
            svlines = [i / 50 for i in range(1, 50)]
            lines = GhostLines(svlines).get_SV(temp) + [SV(temp + 3, 340, 20, 1), SV(temp + 3, 0.01, 20, 1)]
            v += lines
            temp += get_snap(bpm, 1/8)
    return v

def twist(start, end):
    offset, notecount = Noteoffset(NSVFile, start, end)
    v = []
    bpmlinecount = len(offset)
    for i in range(bpmlinecount):
        lines = GhostLines([(j + 1) / bpmlinecount for j in range(i)]).get_SV(offset[i] - 1) + [SV(offset[i] + 3, 340, 20, 1), SV(offset[i] + 3, 0.01, 20, 1)]
        v += lines
    return v

def transition_to_break(start, end):
    offset, notecount = Noteoffset(NSVFile, start, end)
    v = []
    def f(t):
        def match(t, i):
            slope = 1 / get_snap(bpm, 4)
            f = lambda x: slope * (offset[i] - x)
            return f(t) if 0 < f(t) <= 1 else 0.001
        return [match(t, i) for i in range(len(offset))]
    t = start
    while t < end:
        lines = GhostLines(f(t)).get_SV(t) + [SV(t + 3, 340, 20, 1), SV(t + 3, 0.01, 20, 1)]
        v += lines
        t += get_snap(bpm, 1/8)
    return v

def break_with_some_twist(start, end):
    offset, notecount = Noteoffset(NSVFile, start, end)
    random_slopes = [random() * 0.6 + 0.4 for i in offset]
    v = []
    def f(t):
        def match(t, i):
            slope = 1 / get_snap(bpm, 4) * random_slopes[i]
            f = lambda x: slope * (offset[i] - x)
            return f(t) if 0 < f(t) <= 1 else 0.001
        return [match(t, i) for i in range(len(offset))]
    t = start
    while t < end:
        lines = GhostLines(f(t)).get_SV(t) + [SV(t + 3, 340, 20, 1), SV(t + 3, 0.01, 20, 1)]
        v += lines
        t += get_snap(bpm, 1/8)
    return v

def even_drum_section4(start, end):
    offset, notecount = Noteoffset(NSVFile, start, end)
    def sinewave_bottom(x, t):
        return (sin((x - t) / get_snap(bpm, 0.5) * pi) ** 2) if abs(x - t) < get_snap(bpm, 0.5) else 0
    
    def sum_sinewave(x):
        return sum([sinewave_bottom(x, t) for t in offset if notecount[offset.index(t)] == 2])
    v = []
    def f(t):
        def match(t, i):
            slope = 1 / get_snap(bpm, 8) * (3 if notecount[i] == 2 else 1)
            f = lambda x: slope * (offset[i] - x)
            return f(t) if 0 < f(t) <= 1 else 0.001
        return [match(t, i) for i in range(len(offset))]
    t = start
    while t < end:
        s = f(t) + [sum_sinewave(t) * 0.01 * k + 0.01 for k in range(1, 16)]
        lines = GhostLines(s).get_SV(t) + [SV(t + 3, 340, 20, 1), SV(t + 3, 0.01, 20, 1)]
        v += lines
        t += get_snap(bpm, 1/8)
    return v

def even_drum_section5(start, end):
    v = []
    temp = start
    offset, notecount = Noteoffset(NSVFile, start, end)
    def sinewave_bottom(x, t):
        return (sin((x - t) / get_snap(bpm, 0.25) * pi) ** 2) if abs(x - t) < get_snap(bpm, 0.25) else 0
    def sum_sinewave(x):
        return sum([sinewave_bottom(x, t) for t in offset if notecount[offset.index(t)] == 2])
    offsets, columns = noteColumn(NSVFile, start, end)
    def f(t):
        def m(t, i):
            if 0 < offsets[i] - t < get_snap(bpm, 2):
                return [(c + 2) * 0.25 - 0.25 / get_snap(bpm, 2) * (get_snap(bpm, 2) + t - offsets[i]) for c in columns[i]]
            return []
        res = []
        for i in range(len(offsets)):
            res += m(t, i)
        return res
    while temp < end:
        svlines = f(temp) + [0.25, 0.5, 0.75, 1]
        svlines = [x * 0.5 + 0.25 for x in svlines]
        lines = GhostLines([i * 0.5 for i in svlines + [sum_sinewave(temp) * 0.048 * k + 0.01 for k in range(1, 6)] + [1 - sum_sinewave(temp) * 0.048 * k - 0.01 for k in range(1, 6)]]).get_SV(temp) + [SV(temp + 3, 340, 20, 1), SV(temp + 3, 0.01, 20, 1)]
        v += lines
        temp += get_snap(bpm, 1/8)
    return v

def polyriddim_2():
    all_sv = [SV(0, bpm, 20, 1)]
    all_sv += intro(1392, 12686)
    all_sv += buildup_0(12686, 23980)
    all_sv += main_1(23980, 35274)
    all_sv += main_stac(35274, 46568)
    all_sv += main_stac_melo(46568, 69156)
    all_sv += [SV(69160, bpm, 20, 1)]
    all_sv += buildup_1(74803, 80449)
    all_sv += even_drum_section1(80450, 91743)
    all_sv += even_drum_section2(91744, 103039)
    all_sv += even_drum_section3(103039, 114333)
    all_sv += twist(114333, 117156)
    all_sv += even_drum_section3(117156, 122803)
    all_sv += transition_to_break(122804, 125583)
    all_sv += break_with_some_twist(125627, 136920)
    all_sv += even_drum_section4(136921, 148215)
    all_sv += even_drum_section5(148215, 159509)
    i = 0
    while len(all_sv) < 80000:
        all_sv.append(SV(159509 + i, bpm, 20, 1))
        all_sv.append(SV(159509 + i, 1, 20, 0))
        i += 5
    print(len(all_sv), "SV Lines has been used in polyriddim 2")
    return all_sv

DecodeToFile(NSVFile, "output.osu", polyriddim_2())