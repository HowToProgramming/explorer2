import numpy as np
from SVEncodeDecode import SV

class GhostLines():
    def __init__(self, bpmlines:list):
        self.lines = sorted(list(set(bpmlines)))
    
    def get_lineset(self):
        if len(self.lines) > 0:
            line_set = [self.lines[0]]
            for i in range(1, len(self.lines)):
                line_set.append(self.lines[i] - self.lines[i-1])
            line_set += [10]
            return line_set
        return []
    
    def add_lines(self, lines):
        t = self
        t.lines += lines
        t.lines = sorted(list(set(t.lines)))
        return t
    
    def get_SV(self, offset):
        lineset = self.get_lineset()
        bpm = 11000000
        ofs_per_beat = 60000 / bpm
        SVs = [SV(offset - 1, 0.001, 20, 1), SV(offset, bpm, 20, 1)]
        for i, line in enumerate(lineset):
            SVs.append(SV(offset + ofs_per_beat * i * 4, line, 20, 0))
        return SVs
    
    def get_classic_bpm(self, offset):
        lineset = self.get_lineset()
        bpm_main = 10000
        startofs = offset - len(lineset) * 5
        SVs = [SV(startofs - 5, 0.001, 20, 1)]
        for i in range(len(lineset)):
            bpm = bpm_main * lineset[i]
            SVs.append(SV(startofs + 5 * i, bpm, 20, 1))
        SVs.append(SV(offset, 0.001, 20, 1))
        return SVs

class functionLines():
    def __init__(self, functions:list): # all functions will be rendered in range 0-1
        self.functions = functions.copy()
    
    def get_out_values(self, value):
        return list(map(lambda func: func(value), self.functions))

    def render(self, start, end, fps=30):
        SVs = []
        frequency = 1000 / fps
        slope = 1 / (end - start)
        in_val = 0
        temp = start
        while in_val < 1:
            out_val = self.get_out_values(in_val)
            SVs += GhostLines(out_val).get_SV(temp)
            temp += frequency
            in_val += slope * frequency
        return SVs