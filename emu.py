#!/bin/python3
import argparse
import sys
import time

DECODER_ROM_FILES = ['rom/decoder0.bin', 'rom/decoder1.bin', 'rom/decoder2.bin']
MEMSIZE = 65536

def inc16(w):
    return (w + 1) & 0xFFFF

class Memory():
    PERIPH = 0xF000
    def __init__(self):
        self.mem = [0] * MEMSIZE
        for b in range(MEMSIZE):
            self.mem[b] = 0xFF

    def __getitem__(self, addr):
        if addr < Memory.PERIPH:
            return self.mem[addr]
        else:
            return 0

    def __setitem__(self, addr, value):
        if isinstance(addr, slice):
            for vi,ai in enumerate(range(addr.start, addr.stop)):
                self.mem[ai] = value[vi]
            return

        if addr < Memory.PERIPH:
            self.mem[addr] = value
        elif addr == 0xF000: #uart
            sys.stdout.write(chr(value))
            sys.stdout.flush()

def decoder_rom(file):
    with open(file, 'rb') as f:
            data = f.read()
    return data

class CPU():
    def __init__(self):
        self.verbose = False
        self.mem = Memory()
        self.halted = False

        self.dec0 = decoder_rom(DECODER_ROM_FILES[0])
        self.dec1 = decoder_rom(DECODER_ROM_FILES[1])
        self.dec2 = decoder_rom(DECODER_ROM_FILES[2])

        self.tick = 0
        self.Cint = 0   # internal carry
        self.C = 0      # user flags: carry, zero, negative
        self.Z = 0
        self.N = 0
        
        self.pc = 0     # program counter
        self.a = 0      # address buffer
        self.t = 0      # t register
        self.regnames = ['bh', 'bl', 'ch', 'cl', 'x', 'y', 'sh', 'sl']
        self.regs = [0] * len(self.regnames)

        self.cycles = 0     # stats
        self.instructions = 0

    def run(self):
        self.pc = 0
        self.tick = 0
        self.opcode = 0x00
        self.instruction_bytes = []

        while not self.halted:
            self.clock()

        self.print_instruction() # Print final instruction


    def clock(self):

        # decode

        flagbits = self.N << 2 | self.Z << 1 | self.C
        address = flagbits << 12 | (self.opcode & 0xFF) << 4 | (self.tick & 0xF)
        d0 = self.dec0[address]
        d1 = self.dec1[address]
        d2 = self.dec2[address]

        sig_next = not (d0 & 0b1)
        if sig_next:
            self.tick = 0
            self.clock()
            return

        sig_aout  =      d0 & 0b00000010
        sig_pcinc = not (d0 & 0b00000100)
        sig_pcwr  = not (d0 & 0b00001000)
        sig_irwr  = not (d0 & 0b00010000)
        sig_memrd = not (d0 & 0b00100000)
        sig_memwr = not (d0 & 0b01000000)
        sig_ainc  = not (d0 & 0b10000000)

        sig_ahwr  = not (d1 & 0b00000001)
        sig_alwr  = not (d1 & 0b00000010)
        sig_regoe = not (d1 & 0b00000100)
        sig_regwr = not (d1 & 0b00001000)
        sig_opsel = d1 >> 4

        sig_regsel = d2 & 0b111
        sig_alu    =   not (d2 & 0b00001000)
        sig_twr    =       (d2 & 0b00010000)
        sig_setflags = not (d2 & 0b00100000)


        # execute

        if self.opcode == 0xFF:
            self.halted = True
            return

        abus = self.a if sig_aout else self.pc

        # dbus writers
        if sig_memrd:
            dbus = self.mem[abus]
            if not sig_irwr and not sig_aout:
                self.instruction_bytes.append(dbus)
        elif sig_alu:
            alu_a = self.regs[sig_regsel] if sig_regoe else 0
            dbus = self.alu(alu_a, sig_opsel, sig_setflags)

        # dbus readers
        if sig_memwr:
            self.mem[abus] = dbus
        if sig_irwr:
            # Load new instruction
            self.opcode = dbus
            self.instructions += 1
            self.print_instruction()
            self.instruction_bytes = [abus, dbus]
        if sig_ahwr:
            self.a &= 0x00FF
            self.a |= dbus << 8
        if sig_alwr:
            self.a &= 0xFF00
            self.a |= dbus
        if sig_twr:
            self.t = dbus
        if sig_regwr:
            self.regs[sig_regsel] = dbus

        if sig_pcwr:
            self.pc = abus

        if sig_pcinc:
            self.pc = inc16(self.pc)
        if sig_ainc:
            self.a = inc16(self.a)

        self.tick = (self.tick + 1) % 16
        self.cycles += 1

    def alu(self, a, opsel, setflags):
        b = self.t
        cin = self.C if setflags else self.Cint
        c = 0

        if opsel == 0: # a
            q = a
        elif opsel == 1: # b
            q = b
        elif opsel == 2: # add
            q = a + b
            c = q > 255
        elif opsel == 3: # sub
            q = a + ~b + 1
            c = q >= 0
        elif opsel == 4: # adc
            q = a + b + cin
            c = q > 255
        elif opsel == 5: # sbc
            q = a + ~b + cin
            c = q >= 0
        elif opsel == 6: # and
            q = a & b
        elif opsel == 7: # or
            q = a | b
        elif opsel == 8: # xor
            q = a ^ b
        elif opsel == 9: # inc if carry set
            q = a + cin
        elif opsel == 10: # inc
            q = a + 1
            c = q > 255
        elif opsel == 11: # dec 
            q = a - 1
            c = q >= 0
        elif opsel == 12: # dec if carry clear
            q = a + ~0 + cin
        elif opsel == 13:
            q = a << 1
            c = q > 255
        else:
            print(f"Error: invalid ALU op {opsel}")
            sys.exit(-1)

        q &= 0xFF

        # Set flags if the operator allows it
        canset = opsel in [2,3,4,5,6,7,8,10,11,13]
        if canset:
            if setflags:
                self.C = c
                self.Z = (q == 0)
                self.N = bool(q & 0x80)
            else:
                self.Cint = c

        return q


    def print_instruction(self):
        if not self.verbose: return
        if len(self.instruction_bytes) < 2: return
        addr = self.instruction_bytes[0]
        byteshex = ' '.join([f"{x:02x}" for x in self.instruction_bytes[1:]])
        print(f'\t{addr:04x}  {byteshex:9s}')# {self.name} {self.operands}')        

    def dumpmem(self, start, bytes):
        for i in range(bytes):
            if i % 16 == 0: print(f"\n{start+i:04x}  ", end="")
            b = self.mem[start+i]
            print(f"{b:02x} ", end="")
        print("\n")

    def dumpregs(self):
        print('Registers:')
        for i in range(len(self.regs)):
            reg = self.regnames[i]
            val = self.regs[i]
            print('    {0:3s} 0x{1:02x}  {1}'.format(reg, val))
        print('-------------')
        print(f"flags  {'C' if self.C else '.'}{'Z' if self.Z else '.'}{'N' if self.N else '.'}")
        print('    a  0x{0:04x}  {0}'.format(self.a))
        print('    t  0x{0:02x}    {0}'.format(self.t))
        print('    b  0x{0:04x}  {0}'.format(self.regs[0]<<8 | self.regs[1]))
        print('    c  0x{0:04x}  {0}'.format(self.regs[2]<<8 | self.regs[3]))
        print('   pc  0x{0:04x}  {0}'.format(self.pc))
        print('   sp  0x{0:04x}  {0}'.format(self.regs[6]<<8 | self.regs[7]))
        

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="emulator")
    parser.add_argument('file')
    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-r', '--dump_registers', action="store_true")
    args = parser.parse_args()

    with open(args.file, 'rb') as f:
        data = f.read()

    if len(data) > MEMSIZE:
        print("Image is too large.")
        sys.exit(-1)

    cpu = CPU()
    cpu.verbose = args.verbose
    cpu.mem[0:len(data)] = data
    cpu.run()

    print(f"\n---\nStatistics:")
    print(f"    {cpu.instructions} instructions")
    print(f"    {cpu.cycles} cycles")
    cpufreq = 2000000
    cputime = cpu.cycles / cpufreq
    print(f"    {cputime} sec at {cpufreq/1E6} MHz")
    cperi = cpu.cycles / cpu.instructions
    print(f"    {cperi:.2f} cycles/inst")

    if args.dump_registers:
        cpu.dumpregs()

    # cpu.dumpmem(0x005b, 8)
    # cpu.dumpmem(0x3ff0, 512)