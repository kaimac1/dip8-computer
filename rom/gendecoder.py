from pprint import pprint
from collections import namedtuple
import binascii
import sys

from instructions import *

flagbits = 3
cyclebits = 4
inbits = 16
default_seq = [['']] * (2**cyclebits)

def create_flags(flagcode):
    out = namedtuple('flags', ('C', 'Z', 'N'))
    out.C = bool(flagcode & 1)
    out.Z = bool(flagcode & 2)
    out.N = bool(flagcode & 4)
    return out

def create_address(opcode, cycle, flags):
    if cycle > (2**cyclebits -1): raise Exception()
    if opcode > 255: raise Exception()

    return flags.N << 14 | flags.Z << 13 | flags.C << 12 | (opcode << cyclebits) | cycle

def create_data(sigs):
    data = 0
    for i,s in enumerate(signal_names):
        if invert[i]:
            data |= ((s not in sigs)<<i)
        else:
            data |= ((s in sigs)<<i)
    return data

def create_logisim_file(filename, rom):
    with open(filename, 'w') as f:
        f.write("v2.0 raw\n")
        for word in rom:
            f.write("{} ".format(hex(word)[2:]))



invert = [sig.startswith("!") for sig in output_signals]
signal_names = [sig.strip("!") for sig in output_signals] # without !

class Cycle:
    def __init__(self):
        self.condition = lambda flags: True
        self.signals_met = []
        self.signals_unmet = []

fetch_cycle = Cycle()
fetch_cycle.signals_met = t0
next_cycle = Cycle()
next_cycle.signals_met = ['next']

class Instruction:
    def __init__(self):
        self.sequence = [fetch_cycle] # list of Cycles

default_instruction = Instruction()


def get_signals(sigs):
    sigsout = []

    for sig in sigs:
        if sig not in raw_signals:
            print (f"ERROR 0x{opcode:02x}: Undefined signal '{sig}'")
            sys.exit(-1)

        # Replace individual ALU op/register selection signals with multiplexed regsel/opsel bits
        if sig in regsel:
            regnum = regsel.index(sig)
            if regnum & 1: sigsout.append('regsel0')
            if regnum & 2: sigsout.append('regsel1')
            if regnum & 4: sigsout.append('regsel2')
        elif sig in alusel:
            opnum = alusel.index(sig)
            if opnum & 1: sigsout.append('opsel0')
            if opnum & 2: sigsout.append('opsel1')
            if opnum & 4: sigsout.append('opsel2')
            if opnum & 8: sigsout.append('opsel3')
        else:
            sigsout.append(sig)

    return sigsout




def main():
    instructions = {}

    for opcode in inst:
        text = inst[opcode]
        instruction = Instruction()


        lines = [line.strip() for line in text.split('\n')]
        name = lines[0]
        cycles = lines[1:]

        for c in cycles:
            this_cycle = Cycle()
            sigsout = []
            words = [word for word in c.split(" ") if word != '']

            if words[0][0] == '(':
                colon_pos = words.index(':')
                then_words = words[1:colon_pos]
                else_words = words[colon_pos+1:]
                cond = words[0]

                # somewhat hacky!
                if cond == '(C=1)': this_cycle.condition = lambda flags: flags.C
                if cond == '(C=0)': this_cycle.condition = lambda flags: not flags.C
                if cond == '(Z=1)': this_cycle.condition = lambda flags: flags.Z
                if cond == '(Z=0)': this_cycle.condition = lambda flags: not flags.Z
                if cond == '(N=1)': this_cycle.condition = lambda flags: flags.N
                if cond == '(N=0)': this_cycle.condition = lambda flags: not flags.N
                if cond == '(Z=1,N=1)': this_cycle.condition = lambda flags: flags.Z and flags.N

                this_cycle.signals_met = get_signals(then_words)
                this_cycle.signals_unmet = get_signals(else_words)
            else:
                this_cycle.signals_met = get_signals(words)

            instruction.sequence.append(this_cycle)
        instructions[opcode] = instruction


    rom = [0] * 2**inbits
    
    for flagcode in range(2**flagbits):
        flags = create_flags(flagcode)

        for opcode in range(256):
            if opcode in instructions:
                instruction = instructions[opcode]
                sequence = instruction.sequence.copy()
                sequence.append(next_cycle)
                if len(sequence) >= 2**cyclebits:
                    raise Exception(f"Instruction sequence too long: 0x{opcode:02x}")
            else:
                # Unimplemented instruction
                instruction = default_instruction
                sequence = instruction.sequence.copy()

            #if opcode == 0xfe: print(opcode, seq)

            for cycle in range(2**cyclebits):
                if cycle < len(sequence):
                    this_cycle = sequence[cycle]
                    sigs = this_cycle.signals_met if this_cycle.condition(flags) else this_cycle.signals_unmet
                else:
                    sigs = ['next']

                addr = create_address(opcode, cycle, flags)
                data = create_data(sigs)
                rom[addr] = data


    print('Output signals:')
    for i,s in enumerate(output_signals):
        print(f"{i:3d} {s}")

    print(f"\n{len(output_signals)} output signals")
    print(f"{len(instructions)} opcodes\n")
            
    create_logisim_file("decoder_logisim.rom", rom)

    byte0 = bytearray([word & 0xFF for word in rom])
    with open('decoder0.bin', 'wb') as f:
        f.write(byte0)

    byte1 = bytearray([(word >> 8) & 0xFF for word in rom])
    with open('decoder1.bin', 'wb') as f:
        f.write(byte1)

    byte2 = bytearray([(word >> 16) & 0xFF for word in rom])
    with open('decoder2.bin', 'wb') as f:
        f.write(byte2)

main()
