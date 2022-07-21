#!/bin/python3
import argparse
import sys
import binascii

#DECODER_ROM_FILES = ['../rom/decoder0.bin', '../rom/decoder1.bin', '../rom/decoder2.bin']

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

class CPU():
    def __init__(self):
        self.verbose = False
        self.mem = Memory()
        self.halted = False
        self.pc = 0
        self.sp = 0
        self.a = 0
        self.t = 0
        self.C = 0
        self.Z = 0
        self.N = 0

        self.regnames = ['bh', 'bl', 'ch', 'cl', 'x', 'y']
        self.regs = dict(zip(self.regnames, [0] * len(self.regnames)))

        self.opcodes = {
            (0x00, 0x12): self.adr,
            (0x13, 0x13): self.adra,

            (0x14, 0x15): self.jmp,
            (0x16, 0x17): self.jcs,
            (0x18, 0x19): self.jcc,
            (0x1a, 0x1b): self.jz,
            (0x1c, 0x1d): self.jnz,
            (0x1e, 0x1e): self.ret,

            (0x1f, 0x1f): self.stl,
            (0x20, 0x20): self.ldx,
            (0x21, 0x21): self.ldy,
            (0x22, 0x22): self.ldb,
            (0x23, 0x23): self.ldc,
            (0x24, 0x24): self.ldbh,
            (0x25, 0x25): self.ldbl,
            (0x26, 0x26): self.ldch,
            (0x27, 0x27): self.ldcl,
            (0x28, 0x28): self.stx,
            (0x29, 0x29): self.sty,
            (0x2a, 0x2a): self.stb,
            (0x2b, 0x2b): self.stc,
            (0x2c, 0x2c): self.stbh,
            (0x2d, 0x2d): self.stbl,
            (0x2e, 0x2e): self.stch,
            (0x2f, 0x2f): self.stcl,

            (0x30, 0x33): self.push,
            (0x34, 0x37): self.pop,
            (0x38, 0x38): self.pushl,
            (0x39, 0x3c): self.movstack,
            
            (0x40, 0x63): self.mov,
            (0x64, 0x6a): self.movt,
            (0x6b, 0x6e): self.movbc,
            (0x6f, 0x6f): self.ldt,
            
            (0x70, 0x7f): self.add,
            (0x80, 0x8f): self.sub,
            (0x90, 0x9f): self.adc,
            (0xa0, 0xaf): self.sbc,
            (0xb0, 0xbf): self.cmp,
            (0xc0, 0xcb): self.opand,
            (0xd0, 0xdb): self.opor,
            (0xe0, 0xeb): self.xor,
            (0xf0, 0xf3): self.inc,
            (0xf4, 0xf7): self.dec,
            
            (0xff, 0xff): self.brk,
        }

    def brk(self):
        #print("Halted!")
        self.halted = True

    def b16(self):
        return self.regs['bh'] << 8 | self.regs['bl']
    def c16(self):
        return self.regs['ch'] << 8 | self.regs['cl']

    def getreg(self, reg):
        if reg == 'b':
            return self.b16()
        elif reg == 'c':
            return self.c16()
        elif reg == 'sp':
            return self.sp
        else:
            return self.regs[reg]

    def adr(self):
        r = ['b', 'c', 'sp']
        mode = self.ib - 0x00
        if mode == 0:
            al = self.next()
            ah = self.next()
            self.a = ah<<8 | al
            self.operands = f"${self.a:04x}"

        elif mode < 4:
            self.a = self.getreg(r[mode-1])
        elif mode < 7:
            offset = self.next()
            self.a = self.getreg(r[mode-4])
        elif mode < 10:
            ol = self.next()
            oh = self.next()
            offset = oh<<8 | ol
            self.a = self.getreg(r[mode-7]) + offset
        elif mode < 0xd:
            self.a = self.getreg(r[mode-0xa]) + self.regs['x']
        elif mode < 0x10:
            self.a = self.getreg(r[mode-0xd]) + self.regs['y']
        elif mode == 0x10:
            self.a = self.sp + self.b16()
        elif mode == 0x11:
            self.a = self.sp + self.c16()
        elif mode == 0x12:
            self.a = self.b16() + self.c16()

    def adra(self):
        lo = self.mem[self.a]
        hi = self.mem[self.a+1]
        self.a = hi<<8 | lo

    def stl(self):
        value = self.next()
        self.mem[self.a] = value
        self.operands = f"${value:02x}"

    def ldx(self):
        self.regs['x'] = self.mem[self.a]
    def ldy(self):
        self.regs['y'] = self.mem[self.a]
    def ldb(self):
        self.regs['bl'] = self.mem[self.a]
        self.a += 1
        self.regs['bh'] = self.mem[self.a]
    def ldc(self):
        self.regs['cl'] = self.mem[self.a]
        self.a += 1
        self.regs['ch'] = self.mem[self.a]
    def ldbh(self):
        self.regs['bh'] = self.mem[self.a]
    def ldbl(self):
        self.regs['bl'] = self.mem[self.a]
    def ldch(self):
        self.regs['ch'] = self.mem[self.a]
    def ldcl(self):
        self.regs['cl'] = self.mem[self.a]

    def stx(self):
        self.mem[self.a] = self.regs['x']
    def sty(self):
        self.mem[self.a] = self.regs['y']
    def stb(self):
        self.mem[self.a] = self.regs['bl']
        self.a += 1
        self.mem[self.a] = self.regs['bh']
    def stc(self):
        self.mem[self.a] = self.regs['cl']
        self.a += 1
        self.mem[self.a] = self.regs['ch']
    def stbh(self):
        self.mem[self.a] = self.regs['bh']
    def stbl(self):
        self.mem[self.a] = self.regs['bl']
    def stch(self):
        self.mem[self.a] = self.regs['ch']
    def stcl(self):
        self.mem[self.a] = self.regs['cl']


    def stack_pop(self):
        self.incsp()
        return self.mem[self.sp]
    def stack_push(self, v):
        self.mem[self.sp] = v
        self.decsp()

    def incsp(self):
        self.sp += 1
        self.sp %= 65536
    def decsp(self):
        self.sp -= 1
        self.sp %= 65536

    def pushreg(self, reg):
        if reg in ['x', 'y', 'bh', 'bl', 'ch', 'cl']:
            self.stack_push(self.regs[reg])
        elif reg == 'b':
            self.pushreg('bl')
            self.pushreg('bh')
        elif reg == 'c':
            self.pushreg('cl')
            self.pushreg('ch')

    def popreg(self, reg):
        if reg in ['x', 'y', 'bh', 'bl', 'ch', 'cl']:
            self.regs[reg] = self.stack_pop()
        elif reg == 'b':
            self.popreg('bh')
            self.popreg('bl')
        elif reg == 'c':
            self.popreg('ch')
            self.popreg('cl')


    def push(self):
        nib = lonib(self.ib)
        regs = ['x', 'y', 'b', 'c']
        self.pushreg(regs[nib])
        self.operands = regs[nib]

    def pushl(self):
        # big-endian in the instruction
        hi = self.next()
        lo = self.next()
        # little-endian on the stack
        self.stack_push(hi)
        self.stack_push(lo)
        self.operands = f"${hi<<8|lo:04x}"

    def pop(self):
        idx = lonib(self.ib) - 4
        regs = ['x', 'y', 'b', 'c']
        self.popreg(regs[idx])
        self.operands = regs[idx]

    def movstack(self):
        self.name = 'mov'
        if self.ib == 0x39:
            self.sp = self.b16()
            self.operands = 'sp, b'
        elif self.ib == 0x3a:
            self.sp = self.c16()
            self.operands = 'sp, c'
        elif self.ib == 0x3b:
            self.regs['bh'] = self.sp >> 8
            self.regs['bl'] = self.sp & 0xFF
            self.operands = 'b, sp'
        elif self.ib == 0x3c:
            self.regs['ch'] = self.sp >> 8
            self.regs['cl'] = self.sp & 0xFF
            self.operands = 'c, sp'


    def dojump(self, do):
        nib = lonib(self.ib) % 2
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
        lo = self.stack_pop()
        hi = self.stack_pop()
        addr = lo | (hi << 8)
        self.pc = addr


    # mov

    def mov(self):
        regs = ['bh', 'bl', 'ch', 'cl', 'x', 'y']
        dest = (self.ib - 0x40) // 6
        src  = (self.ib - 0x40) %  6
        if src == dest: # load literal
            literal = self.next()
            self.regs[regs[dest]] = literal
            self.operands = f"{regs[dest]}, {literal}"
        else:
            self.regs[regs[dest]] = self.regs[regs[src]]
            self.operands = f"{regs[dest]}, {regs[src]}"

    def movt(self):
        self.name = 'mov'
        regs = ['bh', 'bl', 'ch', 'cl', 'x', 'y']
        idx = lonib(self.ib) - 4
        if idx == 6: # load literal
            literal = self.next()
            self.t = literal
            self.operands = f"t, {literal}"
        else:
            src = regs[idx]
            self.t = self.regs[src]
            self.operands = f"t, {src}"

    def movbc(self):
        self.name = 'mov'
        if self.ib == 0x6b:
            self.regs['bh'] = self.regs['ch']
            self.regs['bl'] = self.regs['cl']
            self.operands = "b, c"
        elif self.ib == 0x6c:
            self.regs['ch'] = self.regs['bh']
            self.regs['cl'] = self.regs['bl']
            self.operands = "c, b"
        elif self.ib == 0x6d:
            self.regs['bl'] = self.next()
            self.regs['bh'] = self.next()
            self.operands = f"b, ${self.b16():04x}"
        elif self.ib == 0x6e:
            self.regs['cl'] = self.next()
            self.regs['ch'] = self.next()
            self.operands = f"c, ${self.c16():04x}"

    def ldt(self):
        self.t = self.mem[self.a]

    # alu

    def aluargs(self):
        regs = ['x', 'y', 'bh', 'bl', 'ch', 'cl']
        reg = regs[lonib(self.ib // 2) % 8]
        if self.ib % 2 == 0:
            v2 = self.t
            self.operands = f"{reg}, t"
        else:
            v2 = self.next()
            self.operands = f"{reg}, {v2}"
        return reg, v2


    def flags(self, val):
        self.Z = (val == 0)
        self.N = bool(val & 0x80)

    def add(self):
        reg, v2 = self.aluargs()
        q = self.regs[reg] + v2
        self.C = (q > 255)
        self.regs[reg] = q % 256
        self.flags(self.regs[reg])

    def sub(self):
        reg, v2 = self.aluargs()
        q = self.regs[reg] + ~v2 + 1
        self.C = (self.regs[reg] >= v2)
        self.regs[reg] = q % 256
        self.flags(self.regs[reg])

    def adc(self):
        reg, v2 = self.aluargs()
        q = self.regs[reg] + v2 + int(self.C)
        self.C = (q > 255)
        self.regs[reg] = q % 256
        self.flags(self.regs[reg])

    def sbc(self):
        reg, v2 = self.aluargs()
        q = self.regs[reg] + ~v2 + int(self.C)
        self.C = (self.regs[reg] >= v2)
        self.regs[reg] = q % 256
        self.flags(self.regs[reg])

    def cmp(self): # subtract without storing result
        reg, v2 = self.aluargs()
        q = self.regs[reg] + ~v2 + 1
        self.C = (self.regs[reg] >= v2)
        self.flags(q)

    def opand(self):
        self.name = 'and'
        reg, v2 = self.aluargs()
        self.regs[reg] = self.regs[reg] & v2
        self.flags(self.regs[reg])

    def opor(self):
        self.name = 'or'
        reg, v2 = self.aluargs()
        self.regs[reg] = self.regs[reg] | v2
        self.flags(self.regs[reg])

    def xor(self):
        reg, v2 = self.aluargs()
        self.regs[reg] = self.regs[reg] ^ v2
        self.flags(self.regs[reg])

    def inc(self):
        r = ['x', 'y', 'bl', 'cl']
        idx = self.ib % 4
        reg = r[idx]
        self.regs[reg] = (self.regs[reg] + 1) % 256
        self.flags(self.regs[reg])
        if idx == 2 and self.regs['bl'] == 0: self.regs['bh'] = (self.regs['bh'] + 1) % 256
        if idx == 3 and self.regs['cl'] == 0: self.regs['ch'] = (self.regs['ch'] + 1) % 256
        self.operands = reg

    def dec(self):
        r = ['x', 'y', 'bl', 'cl']
        idx = self.ib % 4
        reg = r[idx]
        self.regs[reg] = (self.regs[reg] - 1) % 256
        self.flags(self.regs[reg])
        if idx == 2 and self.regs['bl'] == 255: self.regs['bh'] = (self.regs['bh'] - 1) % 256
        if idx == 3 and self.regs['cl'] == 255: self.regs['ch'] = (self.regs['ch'] - 1) % 256
        self.operands = reg






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
        print('    a  0x{0:04x}  {0}'.format(self.a))
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

            execd = False
            for oprange in self.opcodes:
                opcode = self.opcodes[oprange]

                if oprange[0] <= self.ib <= oprange[1]:
                    self.name = opcode.__name__
                    opcode()
                    execd = True
                    if self.verbose:
                        self.this_instruction_bytes = ' '.join([f"{x:02x}" for x in self.this_instruction_bytes])
                        print(f'{ipc:04x}  {self.this_instruction_bytes:9s} {self.name} {self.operands}')
                    break

            if not execd:
                print(f"Invalid opcode {self.ib:02x}, halted.")
                return

    

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

    if cpu.verbose:
        cpu.dumpmem(0,32)
    cpu.run()

    if args.dump_registers:
        cpu.dumpregs()

    if cpu.verbose:
        cpu.dumpmem(0,32)