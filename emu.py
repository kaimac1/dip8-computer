#!/bin/python3
import argparse
import sys
import binascii

MEMSIZE = 65536

# Low nibble
def lonib(b):
    return b & 0x0f
def hinib(b):
    return b >> 4

def wrap16(b):
    return b & 0xffff


class Memory():
    PERIPH = 0xF000
    def __init__(self):
        self.mem = [0] * MEMSIZE
        for b in range(MEMSIZE):
            self.mem[b] = 0xFF

    def __getitem__(self, addr):
        if addr < Memory.PERIPH:
            return self.mem[addr]

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

class CPU():
    def __init__(self):
        self.verbose = False
        self.mem = Memory()
        self.halted = False
        self.pc = 0
        self.sp = 0
        self.t = 0
        self.C = 0
        self.Z = 0
        self.N = 0

        self.regnames = ['a', 'bh', 'bl', 'ch', 'cl', 'x', 'y', 'z']
        self.regs = dict(zip(self.regnames, [0] * len(self.regnames)))

        self.opcodes = {
            (0x00, 0x05): self.lda,
            (0x06, 0x0b): self.ldz,
            (0x10, 0x15): self.sta,
            (0x16, 0x1b): self.stz,
            
            (0x20, 0x26): self.push,
            (0x27, 0x2c): self.pop,
            
            (0x30, 0x32): self.jmp,
            (0x33, 0x35): self.jcs,
            (0x36, 0x38): self.jcc,
            (0x39, 0x3b): self.jnz,
            (0x3c, 0x3e): self.jz,
            (0x3f, 0x3f): self.ret,
            
            (0x40, 0x42): self.ldb,
            (0x43, 0x43): self.stb,
            (0x44, 0x46): self.ldc,
            (0x47, 0x47): self.stc,
            (0x48, 0x4b): self.inc,
            (0x4c, 0x4f): self.dec,
            
            (0x50, 0x8f): self.mov,
            (0x90, 0x98): self.movt,
            
            (0xa0, 0xa7): self.add,
            (0xa8, 0xaf): self.sub,
            (0xb0, 0xb7): self.adc,
            (0xb8, 0xbf): self.sbc,
            (0xc0, 0xc7): self.opand,
            (0xc8, 0xcf): self.opor,
            (0xd0, 0xd7): self.xor,
            (0xd8, 0xdf): self.cmp,

            (0xff, 0xff): self.halt,
        }

    def halt(self):
        #print("Halted!")
        self.halted = True

    def b16(self):
        return self.regs['bh'] << 8 | self.regs['bl']
    def c16(self):
        return self.regs['ch'] << 8 | self.regs['cl']
        
    def common_ldaz(self, dest):
        nib = lonib(self.ib) % 6
        if nib == 0:
            lo = self.next()
            hi = self.next()
            addr = lo | (hi << 8)
            self.regs[dest] = self.mem[addr]
            self.operands = addr
        elif nib == 2:
            self.regs[dest] = self.mem[self.b16()]
            self.operands = 'b'
        elif nib == 3:
            self.regs[dest] = self.mem[self.c16()]
            self.operands = 'c'
        elif nib == 4:
            self.regs[dest] = self.mem[self.b16() + self.t]
            self.operands = 'b+t'
        elif nib == 5:
            self.regs[dest] = self.mem[self.c16() + self.t]
            self.operands = 'c+t'

    def common_staz(self, src):
        nib = lonib(self.ib) % 6
        if nib == 0:
            lo = self.next()
            hi = self.next()
            addr = lo | (hi << 8)
            self.mem[addr] = self.regs[src]
        elif nib == 2:
            self.mem[self.b16()] = self.regs[src]
        elif nib == 3:
            self.mem[self.c16()] = self.regs[src]
        elif nib == 4:
            self.mem[self.b16() + self.t] = self.regs[src]
        elif nib == 5:
            self.mem[self.c16() + self.t] = self.regs[src]

    def lda(self):
        self.common_ldaz('a')
    def ldz(self):
        self.common_ldaz('z')
    def sta(self):
        self.common_staz('a')
    def stz(self):
        self.common_staz('z')

    def pushreg(self, reg):
        if reg in ['a', 'x', 'y', 'z', 'bh', 'bl', 'ch', 'cl']:
            self.mem[self.sp] = self.regs[reg]
            self.sp = wrap16(self.sp + 1)
        elif reg == 'b':
            self.pushreg('bl')
            self.pushreg('bh')
        elif reg == 'c':
            self.pushreg('cl')
            self.pushreg('ch')

    def push(self):
        nib = lonib(self.ib)
        if nib == 0:
            lo = self.next()
            hi = self.next()
            self.mem[self.sp] = lo
            self.sp = wrap16(self.sp + 1)
            self.mem[self.sp] = hi
            self.sp = wrap16(self.sp + 1)
            self.operands = f"${hi<<8|lo:04x}"
        else:
            regs = ['a', 'b', 'c', 'x', 'y', 'z']
            self.pushreg(regs[nib - 1])
            self.operands = regs[nib-1]

    def popreg(self, reg):
        if reg in ['a', 'x', 'y', 'z', 'bh', 'bl', 'ch', 'cl']:
            self.sp = wrap16(self.sp - 1)
            self.regs[reg] = self.mem[self.sp]
        elif reg == 'b':
            self.popreg('bh')
            self.popreg('bl')
        elif reg == 'c':
            self.popreg('ch')
            self.popreg('cl')

    def pop(self):
        idx = lonib(self.ib) - 7
        regs = ['a', 'b', 'c', 'x', 'y', 'z']
        self.popreg(regs[idx])
        self.operands = regs[idx]

    def dojump(self, do):
        nib = lonib(self.ib) % 3
        if nib == 0:
            lo = self.next()
            hi = self.next()
            addr = lo | (hi << 8)
            if do:
                self.pc = addr
                self.operands = f"${addr:04x}"
        elif nib == 1:
            if do:
                self.pc = self.b16()
                self.operands = 'b'
        elif nib == 2:
            if do:
                self.pc = self.c16()
                self.operands = 'c'

    def jmp(self):
        self.dojump(True)

    def jcs(self):
        self.dojump(self.C)

    def jcc(self):
        self.dojump(not self.C)

    def jnz(self):
        self.dojump(not self.Z)

    def jz(self):
        self.dojump(self.Z)

    def ret(self):
        self.sp = wrap16(self.sp - 1)
        hi = self.mem[self.sp]
        self.sp = wrap16(self.sp - 1)
        lo = self.mem[self.sp]
        addr = lo | (hi << 8)
        self.pc = addr

    def common_ldbc(self, dest):
        nib = lonib(self.ib) % 4
        if nib == 0:
            lo = self.next()
            hi = self.next()
            self.regs[dest + 'l'] = lo
            self.regs[dest + 'h'] = hi
        elif nib == 1:
            addr = self.b16()
            self.regs[dest + 'l'] = self.mem[addr]
            self.regs[dest + 'h'] = self.mem[addr + 1]
        elif nib == 2:
            addr = self.c16()
            self.regs[dest + 'l'] = self.mem[addr]
            self.regs[dest + 'h'] = self.mem[addr + 1]

    def ldb(self):
        self.common_ldbc('b')
    def ldc(self):
        self.common_ldbc('c')

    def stb(self): #stb c
        addr = self.c16()
        self.mem[addr] = self.regs['bl']
        self.mem[addr+1] = self.regs['bh']

    def stc(self): # stc b
        addr = self.b16()
        self.mem[addr] = self.regs['cl']
        self.mem[addr+1] = self.regs['ch']


    def increg(self, reg):
        self.regs[reg] = (self.regs[reg] + 1) % 256
    def decreg(self, reg):
        self.regs[reg] = (self.regs[reg] - 1) % 256

    def inc(self):
        idx = lonib(self.ib) - 8
        regs = ['bh', 'bl', 'ch', 'cl']
        reg = regs[idx]
        self.increg(reg)
        if self.regs[reg] == 0: # overflow
            if reg == 'bl': self.increg('bh')
            elif reg == 'cl': self.increg('ch')

    def dec(self):
        idx = lonib(self.ib) - 0xc
        regs = ['bh', 'bl', 'ch', 'cl']
        reg = regs[idx]
        self.decreg(reg)
        if self.regs[reg] == 255: # underflow
            if reg == 'bl': self.decreg('bh')
            elif reg == 'cl': self.decreg('ch')


    # mov

    def mov(self):
        regs = ['a', 'bh', 'bl', 'ch', 'cl', 'x', 'y', 'z']
        dest = (self.ib - 0x50) // 8
        src = lonib(self.ib) % 8
        if src == dest: # load literal
            literal = self.next()
            self.regs[regs[dest]] = literal
            self.operands = f"{regs[dest]}, {literal}"
        else:
            self.regs[regs[dest]] = self.regs[regs[src]]
            self.operands = f"{regs[dest]}, {regs[src]}"

    def movt(self):
        self.name = 'mov'
        regs = ['a', 'bh', 'bl', 'ch', 'cl', 'x', 'y', 'z']
        idx = lonib(self.ib)
        if idx == 8: # load literal
            literal = self.next()
            self.t = literal
            self.operands = f"t, {literal}"
        else:
            src = regs[idx]
            self.t = self.regs[src]
            self.operands = f"t, {src}"


    # alu

    def aluarg(self):
        regs = ['a', 'bh', 'bl', 'ch', 'cl', 'x', 'y', 'z']
        reg = regs[lonib(self.ib) % 8]
        self.operands = f"{reg}, t"
        return reg

    def flags(self, reg):
        val = self.regs[reg]
        self.Z = (val == 0)
        self.N = bool(val & 0x80)

    def add(self):
        reg = self.aluarg()
        q = self.regs[reg] + self.t
        self.C = (q > 255)
        self.regs[reg] = q % 256
        self.flags(reg)

    def sub(self):
        reg = self.aluarg()
        q = self.regs[reg] + ~self.t + 1
        self.C = (self.regs[reg] >= self.t)
        self.regs[reg] = q % 256
        self.flags(reg)

    def adc(self):
        reg = self.aluarg()
        q = self.regs[reg] + self.t + int(self.C)
        self.C = (q > 255)
        self.regs[reg] = q % 256
        self.flags(reg)

    def sbc(self):
        reg = self.aluarg()
        q = self.regs[reg] + ~self.t + int(self.C)
        self.C = (self.regs[reg] >= self.t)
        self.regs[reg] = q % 256
        self.flags(reg)

    def opand(self):
        self.name = 'and'
        reg = self.aluarg()
        self.regs[reg] = self.regs[reg] & self.t
        self.flags(reg)

    def opor(self):
        self.name = 'or'
        reg = self.aluarg()
        self.regs[reg] = self.regs[reg] | self.t
        self.flags(reg)

    def xor(self):
        reg = self.aluarg()
        self.regs[reg] = self.regs[reg] ^ self.t
        self.flags(reg)

    def cmp(self): # subtract without storing result
        reg = self.aluarg()
        q = self.regs[reg] + ~self.t + 1
        self.C = (self.regs[reg] >= self.t)
        self.flags(reg)







    def dumpmem(self, start, bytes):
        for i in range(bytes):
            if i % 16 == 0: print(f"\n{start+i:04x}  ", end="")
            b = self.mem[start+i]
            print(f"{b:02x} ", end="")
        print("\n")
        #print(binascii.hexlify(self.mem[start:start+bytes]))
    def dumpregs(self):
        print('----------')
        for reg in self.regs:
            val = self.regs[reg]
            print('{0:3s} 0x{1:02x}  {1}'.format(reg, val))
        print('----------')
        print(f"flags  {'C' if self.C else '.'}{'Z' if self.Z else '.'}{'N' if self.N else '.'}")
        print('    t  0x{0:02x}    {0}'.format(self.t))
        print('    b  0x{0:04x}  {0}'.format(self.regs['bh']<<8 | self.regs['bl']))
        print('    c  0x{0:04x}  {0}'.format(self.regs['ch']<<8 | self.regs['cl']))
        print('   pc  0x{0:04x}  {0}'.format(self.pc))
        print('   sp  0x{0:04x}  {0}'.format(self.sp))
        

    def next(self):
        byte = self.mem[self.pc]
        self.this_instruction_bytes.append(byte)
        self.pc += 1
        self.pc %= MEMSIZE
        return byte

    def run(self):
        while not self.halted:
            self.this_instruction_bytes = []
            self.operands = ""
            ipc = self.pc
            self.ib = self.next()

            for oprange in self.opcodes:
                opcode = self.opcodes[oprange]

                if oprange[0] <= self.ib <= oprange[1]:
                    self.name = opcode.__name__
                    opcode()
                    if self.verbose:
                        self.this_instruction_bytes = ' '.join([f"{x:02x}" for x in self.this_instruction_bytes])
                        print(f'{ipc:04x}  {self.this_instruction_bytes:9s} {self.name} {self.operands}')
                    break

    

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

    cpu.dumpmem(0,32)
    cpu.run()

    if args.dump_registers:
        cpu.dumpregs()

    cpu.dumpmem(0,32)