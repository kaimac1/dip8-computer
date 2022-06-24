#!/bin/python3
import argparse
import sys

addrregs = ['b', 'c']

class Assembler():
    def __init__(self):
        self.pidx = 0
        self.syms = {}

    def get_word(self, text, sep=" "):
        if text == None:
            return None, None
        if sep in text:
            spacepos = text.index(sep)
            word = text[0:spacepos].strip()
            rest = text[spacepos+1:].strip()
        else:
            word = text
            rest = None
        return word, rest        

    def error(self, msg):
        print(f"Error on line {self.line_num}: {msg}")
        sys.exit()

    def write8(self, b):
        self.output.append(b)
        print(f"{self.addr:04x}: wrote 0x{b:02x}")
        self.addr += 1

    def write16(self, dd):
        # Little endian
        self.output.append(dd & 0xFF)
        self.output.append(dd >> 8)
        print(f"{self.addr:04x}: wrote 0x{dd:04x}")
        self.addr += 2




    def is_literal(self, pstr):
        return pstr[0] == '#'

    def get_literal(self, pstr):
        if pstr[0] == '#': pstr = pstr[1:]
        if pstr[0] == '$': val = int(pstr[1:], 16)
        elif pstr[0] == '%': val = int(pstr[1:], 2)
        else:
            try:
                val = int(pstr)
            except:
                if pstr not in self.syms:
                    self.error(f"Undefined symbol: {pstr}")
                val = self.syms[pstr]                    
        return val

    def get_literal8(self, pstr):
        val = self.get_literal(pstr) & 0xFF
        return val

    def get_literal16(self, pstr):
        val = self.get_literal(pstr) & 0xFFFF
        return val
        




    def is_address_reg(self, pstr):
        return pstr in addrregs
    def get_address_reg(self, pstr):
        return addrregs.index(pstr)


    # Stack

    def get_pushpopreg(self, pstr):
        return ['a','b','c','x','y','z'].index(pstr)    

    def inst_push(self, pstr):
        if self.pass1:
            if self.is_literal(pstr): size = 3
            else: size = 1
            return size

        if self.is_literal(pstr):
            self.write8(0x20)
            self.write16(self.get_literal16(pstr))
        else:
            self.write8(0x21 + self.get_pushpopreg(pstr))

    def inst_pop(self, pstr):
        if self.pass1:
            return 1
        self.write8(0x27 + self.get_pushpopreg(pstr))

    # Branch

    def jump_common(self, pstr, base):
        if self.pass1:
            if self.is_address_reg(pstr): size = 1
            else: size = 3
            return size

        if self.is_address_reg(pstr):
            self.write8(base + 1 + self.get_address_reg(pstr))
        else:
            self.write8(base)
            self.write16(self.get_literal16(pstr))

    def inst_jmp(self, pstr):
        return self.jump_common(pstr, 0x30)
    def inst_jcs(self, pstr):
        return self.jump_common(pstr, 0x33)
    def inst_jcc(self, pstr):
        return self.jump_common(pstr, 0x36)
    def inst_jnz(self, pstr):
        return self.jump_common(pstr, 0x39)
    def inst_jz(self, pstr):
        return self.jump_common(pstr, 0x3c)

    def inst_ret(self, pstr):
        if self.pass1: return 1
        self.write8(0x3f)

    # Address regs

    def ldbc_common(self, pstr, base):
        if self.pass1:
            if self.is_literal(pstr): size = 3
            else: size = 1
            return size

        if self.is_literal(pstr):
            self.write8(base)
            self.write16(self.get_literal16(pstr))
        else:
            self.write8(base + 1 + self.get_address_reg(pstr))

    def inst_ldb(self, pstr):
        return self.ldbc_common(pstr, 0x40)
    def inst_ldc(self, pstr):
        return self.ldbc_common(pstr, 0x44)

    def inst_stb(self, pstr):
        if self.pass1:
            return 1

        if pstr == 'c':
            self.write8(0x43)
        else:
            self.error("stb operand must be c")

    def inst_stc(self, pstr):
        if self.pass1:
            return 1

        if pstr == 'b':
            self.write8(0x47)
        else:
            self.error("stc operand must be b")


    # Move

    def get_movareg(self, reg):
        return ['bh', 'bl', 'ch', 'cl', 'x', 'y', 'z'].index(reg)
    def get_movtreg(self, reg):
        return ['bh', 'bl', 'ch', 'cl', 'x', 'y', 'z', 'a'].index(reg)
    def get_movzreg(self, reg):
        return ['bh', 'bl', 'ch', 'cl', 'x', 'y', 'a'].index(reg)
    def get_movregaz(self, reg):
        return ['bh', 'bl', 'ch', 'cl', 'x', 'y'].index(reg)

    def inst_mov(self, pstr):
        if self.pass1:
            return 1

        a, rest = self.get_word(pstr, ",")
        b, _    = self.get_word(rest, ";")

        if a is None or b is None:
            self.error("mov requires two operands")
        if a == 'a':
            self.write8(0x50 + self.get_movareg(b))
        elif a == 't':
            self.write8(0x70 + self.get_movtreg(b))
        elif a == 'z':
            self.write8(0x60 + self.get_movzreg(b))
        else:
            if b == 'a':
                self.write8(0x57 + self.get_movregaz(a))
            elif b == 'z':
                self.write8(0x67 + self.get_movregaz(a))
            else:
                self.error(f"invalid mov instruction")

    
    # ALU

    def get_alureg(self, reg):
        return ['a', 'bh', 'bl', 'ch', 'cl', 'x', 'y', 'z'].index(reg)

    def alu_common(self, pstr, base):
        if self.pass1:
            return 1

        a, rest = self.get_word(pstr, ",")
        b, _    = self.get_word(rest, ";")
        if a is None or b is None:
            self.error("alu instructions require two operands")
        if b != 't':
            self.error("alu instructions require the 2nd operand to be 't'")

        self.write8(base + self.get_alureg(a))


    def inst_add(self, pstr):
        return self.alu_common(pstr, 0x80)
    def inst_sub(self, pstr):
        return self.alu_common(pstr, 0x90)
    def inst_adc(self, pstr):
        return self.alu_common(pstr, 0xa0)
    def inst_sbc(self, pstr):
        return self.alu_common(pstr, 0xb0)
    def inst_and(self, pstr):
        return self.alu_common(pstr, 0xc0)
    def inst_or(self, pstr):
        return self.alu_common(pstr, 0xd0)
    def inst_xor(self, pstr):
        return self.alu_common(pstr, 0xe0)
    def inst_cmp(self, pstr):
        return self.alu_common(pstr, 0xf0)


    # Load/store

    def is_pointer(self, pstr):
        return pstr[0] == "*"

    def is_address_reg_plus_t(self, pstr):
        ar, rest = self.get_word(pstr, "+")
        t, _ = self.get_word(rest)
        return (ar in addrregs) and (t == 't')

    def load_common(self, pstr, base):
        if self.pass1:
            if self.is_literal(pstr): size = 2
            elif self.is_pointer(pstr): size = 3
            elif self.is_address_reg(pstr): size = 1
            elif self.is_address_reg_plus_t(pstr): size = 1
            else: size = 3
            return size

        if self.is_literal(pstr):
            self.write8(base + 0x06)
            self.write8(self.get_literal8(pstr))
        elif self.is_pointer(pstr):
            self.write8(base + 0x01)
            self.write16(self.get_literal16(pstr[1:]))
        elif self.is_address_reg(pstr):
            self.write8(base+ 0x02 + self.get_address_reg(pstr))
        elif self.is_address_reg_plus_t(pstr):
            self.write8(base + 0x04 + self.get_address_reg(pstr[0]))
        else: # absolute
            self.write8(base + 0x00)
            self.write16(self.get_literal16(pstr))

    def store_common(self, pstr, base):
        if self.pass1:
            if self.is_pointer(pstr): size = 3
            elif self.is_address_reg(pstr): size = 1
            elif self.is_address_reg_plus_t(pstr): size = 1
            else: size = 3
            return size

        if self.is_pointer(pstr):
            self.write8(base + 0x01)
            self.write16(self.get_literal16(pstr[1:]))
        elif self.is_address_reg(pstr):
            self.write8(base+ 0x02 + self.get_address_reg(pstr))
        elif self.is_address_reg_plus_t(pstr):
            self.write8(base + 0x04 + self.get_address_reg(pstr[0]))
        else: # absolute
            self.write8(base + 0x00)
            self.write16(self.get_literal16(pstr))

    def inst_lda(self, pstr):
        return self.load_common(pstr, 0x00)
    def inst_ldz(self, pstr):
        return self.load_common(pstr, 0x07)
    def inst_sta(self, pstr):
        return self.load_common(pstr, 0x10)
    def inst_stz(self, pstr):
        return self.load_common(pstr, 0x16)

    def inst_ldt(self, pstr):
        if self.pass1:
            if self.is_literal(pstr): return 1
            self.error("operand to ldt must be literal")
        self.write8(0x0e)
        self.write8(self.get_literal8(pstr))




    def assemble(self, src):
        lines = src.split('\n')

        # pass 1
        print("PASS 1")
        self.addr = 0
        self.pass1 = True
        for i, line in enumerate(lines):
            self.line_num = i+1
            size = self.asm_line(line)
            self.addr += size

        # pass 2
        print("\n\nPASS 2")
        self.output = bytearray()
        self.addr = 0
        self.pass1 = False
        self.line_num = 0
        for i, line in enumerate(lines):
            self.line_num = i+1
            self.asm_line(line)

        return self.output


    def define_symbol(self, name, value):
        if name in self.syms:
            self.error(f"symbol already defined: {name}")
        self.syms[name] = value        

    def is_instruction(self, inst):
        return hasattr(self, "inst_" + inst)

    def run_instruction(self, inst, pstr):
        # Strip comments
        pstr, _ = self.get_word(pstr, ";")
        print(f"inst: `{inst}`, pstr: `{pstr}`")
        return getattr(self, "inst_" + inst)(pstr)

    def asm_line(self, line):
        line = line.strip()
        if line == "": return 0

        first, rest = self.get_word(line)
        if first[0] == ";": return 0 # comment

        method = "inst_" + first
        if self.is_instruction(first):  # unlabelled instruction
            return self.run_instruction(first, rest)
        elif rest is None:
            # just a label
            if self.pass1:
                self.define_symbol(first, self.addr)
                return 0
            return

        # we have a labelled instruction or variable
        name = first
        middle, rest = self.get_word(rest)

        if not self.is_instruction(middle):
            self.error(f"invalid instruction: {middle}")
        
        # Store symbol/label address
        if self.pass1:
            self.define_symbol(name, self.addr)

        return self.run_instruction(middle, rest)
        




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DIP8 assembler")
    parser.add_argument('srcfile')
    parser.add_argument('outfile')
    args = parser.parse_args()

    with open(args.srcfile, 'r') as f:
        src = f.read()

    asm = Assembler()
    out = asm.assemble(src)

    import binascii
    print(f"\nSymbols: {asm.syms}")
    print(f"{len(out)} bytes.\n")

    with open(args.outfile, 'wb') as f:
        f.write(out)

