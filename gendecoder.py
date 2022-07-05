from pprint import pprint
import binascii

from decoder_spec import *

#flags = ['C', 'N', 'Z']
cyclebits = 4
inbits = 16
HALT = 0xFF

invert = [sig.startswith("!") for sig in output_signals]
signal_names = [sig.strip("!") for sig in output_signals] # without !


def create_address(opcode, cycle, flags=[]):
    if cycle > (2**cyclebits -1): raise Exception()
    if opcode > 255: raise Exception()
    return (opcode << cyclebits) | cycle

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
    
    

def main():
    instructions = {}

    for opcode in inst:
        lines = [line.strip() for line in inst[opcode].split('\n')]
        name = lines[0]
        sections = lines[1:]

        # Add T0 fetch signals
        timing = []
        if opcode != HALT:
            timing.append(t0)

        for s in sections:
            sigsout = []
            sigs = [sig for sig in s.split(" ") if sig != '']
            for sig in sigs:
                if sig not in raw_signals:
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
            timing.append(sigsout)

        # Add asynchronous next signal after instruction sequence
        if opcode != HALT:
            timing.append(['next'])

        instructions[opcode] = timing


    rom = [0] * 2**inbits
    
    for opcode in instructions:
        timing = instructions[opcode]
        for cycle in range(2**cyclebits):
            addr = create_address(opcode, cycle)
            if cycle < len(timing):
                data = create_data(timing[cycle])
            else:
                data = create_data([])
            rom[addr] = data

    #print(rom[0:16])


    print('Output signals:')
    for i,s in enumerate(output_signals):
        print(f"{i:3d} {s}")

    print(f"\n{len(output_signals)} output signals")
    print(f"{len(instructions)} opcodes\n")
            
    create_logisim_file("decoder.rom", rom)



main()
