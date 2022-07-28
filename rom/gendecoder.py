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

class Instruction:
    def __init__(self):
        self.sequence_good = []
        self.sequence_bad = []
        self.condition = lambda flags: True


def main():
    instructions = {}

    for opcode in inst:
        text = inst[opcode]

        instruction = Instruction()
        instruction.sequence_good = [t0]
        instruction.sequence_bad = [t0]

        lines = [line.strip() for line in text.split('\n')]
        name = lines[0]
        sections = lines[1:]

        for s in sections:
            sigsout = []
            sigs = [sig for sig in s.split(" ") if sig != '']
            cond = False
            for sig in sigs:

                if sig[0] == '(':
                    if sig == '(CS)': instruction.condition = lambda flags: flags.C
                    if sig == '(CC)': instruction.condition = lambda flags: not flags.C
                    if sig == '(Z)':  instruction.condition = lambda flags: flags.Z
                    if sig == '(NZ)': instruction.condition = lambda flags: not flags.Z
                    if sig == '(S)':  instruction.condition = lambda flags: flags.N
                    if sig == '(NS)': instruction.condition = lambda flags: not flags.N
                    instruction.sequence_bad = instruction.sequence_good.copy()
                    continue

                elif sig not in raw_signals:
                    print (f"ERROR 0x{opcode:02x}: Undefined signal '{sig}'")
                    return False

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

            instruction.sequence_good.append(sigsout)

        instructions[opcode] = instruction


    rom = [0] * 2**inbits
    
    for flagcode in range(2**flagbits):
        flags = create_flags(flagcode)

        for opcode in range(256):

            if opcode in instructions:
                # Select sequence based on whether the condition is met
                instruction = instructions[opcode]
                good = instruction.condition(flags)
                seq = instruction.sequence_good if good else instruction.sequence_bad
                seq = seq + [['next']]
                if len(seq) >= 2**cyclebits:
                    raise Exception("Instruction sequence too long", opcode)
            else:
                # Unimplemented instruction
                seq = default_seq

            #if opcode == 0xfe: print(opcode, seq)

            for cycle in range(2**cyclebits):
                addr = create_address(opcode, cycle, flags)
                if cycle < len(seq):
                    data = create_data(seq[cycle])
                else:
                    data = create_data(['next'])
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
