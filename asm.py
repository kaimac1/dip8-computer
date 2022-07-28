#!/bin/python3
# DIP-8 assembler
# Kyle McInnes 2022

import argparse
import sys
import string

ANSI_RED   = '\x1b[31m'
ANSI_GREEN = '\x1b[92m'
ANSI_RESET = '\x1b[0m'

REGS2 = ['b', 'c']
REGS4 = ['x', 'y', 'b', 'c']
REGS6 = ['x', 'y', 'bh', 'bl', 'ch', 'cl']
REGS7 = ['x', 'y', 'bh', 'bl', 'ch', 'cl', 'm']

LOCAL_LABEL_CHAR = '_'


class Token():
    def __init__(self, toktype, value):
        self.type = toktype
        self.value = value

    def __repr__(self):
        return f"{self.type}({repr(self.value)})"

SYMBOLS = '+[]'

def is_whitespace(char):
    return char in [' ', '\t', ',']
def is_symbol(char):
    return char in SYMBOLS
def is_wordsep(char):
    return char and char in ' \t,' + SYMBOLS
def is_literal_start(char):
    return char in ['#', '$', '%', "'"]

class Tokeniser():
    def __init__(self, input):
        self.str = input
        self.pos = 0

    def error(self, msg):
        print(msg)
        sys.exit(-1)

    def char(self):
        if self.pos >= len(self.str):
            return None
        return self.str[self.pos]
    def nextchar(self):
        self.pos +=1
        return self.char()

    # Expect that the next char is c, and then move one past that
    def expectchar(self, c):
        self.pos += 1
        if self.char() != c:
            self.error(f"Expected {c} at column {self.pos+1}")
        self.pos += 1

    def get_word(self):
        word = ''
        while not is_wordsep(self.char()):
            if not self.char(): break
            word += self.char()
            self.nextchar()
        return word

    def get_literal(self):
        if self.char() == "'": # Character
            v = ord(self.nextchar())
            self.expectchar("'")
            return v
        
        if self.char() == '#': # Ignore #
            self.nextchar()

        if self.char() == '$': # Hex
            self.nextchar()
            v = int(self.get_word(), 16)
            return v
        if self.char() == '%': # Binary
            self.nextchar()
            v = int(self.get_word(), 2)
            return v
        else:
            word = self.get_word()
            try:
                return int(word)
            except:
                return word

    def get_string(self):
        c = self.nextchar()
        out = ""
        while c != '"':
            out += c
            c = self.nextchar()
        self.nextchar()
        return out

    def get_symbol(self):
        c = self.char()
        self.nextchar()
        return c                
    
    def next(self):
        while is_whitespace(self.char()):
            self.pos += 1
        start = self.pos

        c = self.char()
        if c is None:
            return None
        elif c == ';':
            self.pos = len(self.str)
            return None
        elif is_literal_start(c):
            token = Token('literal', self.get_literal())
        elif c == '"':
            token = Token('string', self.get_string())
        elif is_symbol(c):
            token = Token('symbol', self.get_symbol())
        else:
            token = Token('text', self.get_word())

        print(token, end=' ')
        return token





def is_literal(t):
    return t.type == 'literal'



class Assembler():
    def __init__(self):
        self.pidx = 0
        self.syms = {}

    def error(self, msg):
        print(f"Error on line {self.line_num}: {msg}")
        sys.exit(-1)

    def write8(self, b):
        if self.pass1:
            # pass 1 - don't write anything, just calculate size
            self.nbytes += 1
            return

        self.output.append(b)
        print(f"{ANSI_GREEN}[0x{b:02x}]{ANSI_RESET} ", end='')
        self.addr += 1

    def write16(self, dd):
        if self.pass1:
            self.nbytes += 2
            return

        # Little endian
        self.output.append(dd & 0xFF)
        self.output.append(dd >> 8)
        print(f"{ANSI_GREEN}[0x{dd:04x}]{ANSI_RESET} ", end='')
        self.addr += 2

    def get_symbol(self, name):
        local_name = self.parent_label + '/' + name
        if local_name in self.syms:
            return self.syms[local_name]
        elif name in self.syms:
            return self.syms[name]
        else:
            if self.pass1: # don't complain on pass1 if not defined yet
                return 0 
            self.error(f"Undefined symbol: {name}")

    def get_literal(self, t):
        try:
            return int(t.value)
        except:
            if t.value[0] in ['<', '>']:
                name = t.value[1:]
            else:
                name = t.value

            value = self.get_symbol(name)
            if t.value[0] == '<':
                value = value & 0xFF
            elif t.value[0] == '>':
                value = value >> 8
            return value

    def get_literal8(self, t):
        val = self.get_literal(t) & 0xFF
        return val

    def get_literal16(self, t):
        val = self.get_literal(t) & 0xFFFF
        return val
        
    def is_address_reg(self, t):
        return t.type == 'text' and t.value in addrregs
    def get_address_reg(self, t):
        return addrregs.index(t.value)



    # Stack

    def get_pushpopreg(self, t):
        return REGS4.index(t.value)

    def inst_push(self):
        t = self.tok.next()
        if is_literal(t):
            self.write8(0x41)
            # push literal is big-endian
            value = self.get_literal16(t)
            self.write8(value >> 8)
            self.write8(value & 0xFF)
        else:
            self.write8(0x39 + self.get_pushpopreg(t))

    def inst_pop(self):
        t = self.tok.next()
        self.write8(0x3d + self.get_pushpopreg(t))



    # Branch

    def jump_common(self, base):
        self.write8(base)
        self.write16(self.get_literal16(self.tok.next()))

    def inst_jmp(self):
        self.jump_common(0x30)
    def inst_jmpa(self):
        self.write8(0x31)
    def inst_jcs(self):
        self.jump_common(0x32)
    def inst_jcc(self):
        self.jump_common(0x33)
    def inst_jz(self):
        self.jump_common(0x34)
    def inst_jnz(self):
        self.jump_common(0x35)
    def inst_js(self):
        self.jump_common(0x36)
    def inst_jns(self):
        self.jump_common(0x37)
    def inst_ret(self):
        self.write8(0x38)



    # Load / store

    def ldst_common(self, base):
        t = self.tok.next()
        if t:
            self.gen_adr(t)
        self.write8(base)

    def inst_ldt(self):
        self.ldst_common(0x1e)
    def inst_ldx(self):
        self.ldst_common(0x1f)
    def inst_ldy(self):
        self.ldst_common(0x20)
    def inst_ldb(self):
        self.ldst_common(0x21)
    def inst_ldc(self):
        self.ldst_common(0x22)
    def inst_ldbh(self):
        self.ldst_common(0x23)
    def inst_ldbl(self):
        self.ldst_common(0x24)
    def inst_ldch(self):
        self.ldst_common(0x25)
    def inst_ldcl(self):
        self.ldst_common(0x26)

    def inst_stx(self):
        self.ldst_common(0x27)
    def inst_sty(self):
        self.ldst_common(0x28)
    def inst_stb(self):
        self.ldst_common(0x29)
    def inst_stc(self):
        self.ldst_common(0x2a)
    def inst_stbh(self):
        self.ldst_common(0x2b)
    def inst_stbl(self):
        self.ldst_common(0x2c)
    def inst_stch(self):
        self.ldst_common(0x2d)
    def inst_stcl(self):
        self.ldst_common(0x2e)
    def inst_stl(self):
        literal = self.tok.next()
        self.ldst_common(0x2f)
        self.write8(self.get_literal(literal))


    # Move

    def get_movreg(self, reg):
        return REGS6.index(reg)

    def movt_literal(self, t):
        self.write8(0x5b)
        self.write8(self.get_literal8(t))
    def movt_register(self, t):
        offset = self.get_movreg(t.value)
        self.write8(0x55 + offset)
    def movfromt(self, t):
        offset = self.get_movreg(t.value)
        self.write8(0x49 + offset)


    def inst_mov(self):
        ta = self.tok.next()
        tb = self.tok.next()

        if ta is None or tb is None:
            self.error("mov requires two operands")
        if ta.value == tb.value:
            self.error(f"invalid mov instruction")

        # sp moves
        if ta.value == 'sp' or tb.value == 'sp':
            if ta.value == 'sp':
                b_or_c = REGS2.index(tb.value)
                self.write8(0x42 + b_or_c)
            else:
                b_or_c = REGS2.index(ta.value)
                self.write8(0x44 + b_or_c)
            return

        # b/c
        if ta.value in REGS2:
            if tb.type == 'literal':
                b_or_c = REGS2.index(ta.value)
                self.write8(0x5e + b_or_c)
                self.write16(self.get_literal16(tb))
            else:
                if ta.value == 'b' and tb.value == 'c':
                    self.write8(0x5c)
                elif ta.value == 'c' and tb.value == 'b':
                    self.write8(0x5d)
                else:
                    self.error("Bad.")
            return

        if ta.value == 't':
            if tb.type == 'literal':
                self.movt_literal(tb)
            else:
                self.movt_register(tb)
        elif tb.value == 't':
            self.movfromt(ta)
        elif tb.type == 'literal':
            dest = self.get_movreg(ta.value)
            self.write8(0x4f + dest)
            self.write8(self.get_literal8(tb))
        else: # register to register
            self.movt_register(tb)
            self.movfromt(ta)


    # ALU

    def get_alureg(self, reg):
        return REGS7.index(reg)

    def alu_common(self, base):
        # first operand can be:
        #  reg              
        #  m
        #  [ADDR]           -> adr ADDR;        alu m, *
        # second operand can be:
        #  t
        #  #literal
        #  m                -> ldt;             alu *, t
        #  reg2             -> mov t, reg2;     alu *, t
        #  [ADDR]           -> adr ADDR; ldt;   alu *, t
        # both operands cannot be ADDR.

        lit = 0
        dest_in_memory = 0

        ta = self.tok.next()

        if ta.type == 'symbol' and ta.value == '[':
            self.gen_adr(self.tok.next())
            self.tok.next() # eat ]
            dest_in_memory = 1
            op1 = 'm'
        else:
            op1 = ta.value

        tb = self.tok.next()

        if tb.type == 'literal':
            lit = 1
        elif tb.type == 'text':
            if tb.value == 'm':
                self.inst_ldt()
            elif tb.value != 't':
                self.movt_register(tb)
        elif tb.type == 'symbol' and tb.value == '[':
            if dest_in_memory:
                # This is not strictly true - some addressing modes do work
                # But in general, the adr instruction clobbers t
                self.error("Only one ALU operand can be an address.")
            self.gen_adr(self.tok.next())
            self.inst_ldt()
        else:
            self.error("Invalid ALU instruction.")

        self.write8(base + 7*lit + self.get_alureg(op1))
        if lit:
            self.write8(self.get_literal8(tb))

    def arith_common(self, base):
        #ta = self.tok.next()
        #tb = self.tok.next()
        #if ta is None or tb is None:
        #    self.error("ALU instructions require two operands.")
        self.alu_common(base)

    def logic_common(self, base):
        self.arith_common(base)

    def inst_add(self):
        self.arith_common(0x60)
    def inst_sub(self):
        self.arith_common(0x6e)
    def inst_adc(self):
        self.arith_common(0x7c)
    def inst_sbc(self):
        self.arith_common(0x8a)
    def inst_cmp(self):
        self.arith_common(0x98)

    def inst_and(self):
        self.logic_common(0xa6)
    def inst_or(self):
        self.logic_common(0xb4)
    def inst_xor(self):
        self.logic_common(0xc2)

    def inst_ror(self):
        t = self.tok.next()
        if t.value not in REGS6:
            self.error("Invalid operand.")
        self.write8(0xf8 + REGS6.index(t.value))        

    def inst_inc(self):
        t = self.tok.next()
        if t.value not in REGS4:
            self.error("Invalid operand.")
        self.write8(0xf0 + REGS4.index(t.value))

    def inst_dec(self):
        t = self.tok.next()
        if t.value not in REGS4:
            self.error("Invalid operand.")
        self.write8(0xf4 + REGS4.index(t.value))



    def get_aluregw(self, reg):
        return REGS2.index(reg)

    def inst_addw(self):
        ta = self.tok.next()
        tb = self.tok.next()
        if ta is None or tb is None:
            self.error("ALU instructions require two operands.")
                    
        lit = 0
        if tb.type == 'text':
            if tb.value == 'm':
                self.inst_ldt()
                offs = 0
            elif tb.value == 't':
                offs = 0
            elif tb.value in ['b', 'c']:
                offs = 1 if tb.value == 'b' else 2
            else:
                self.error("Invalid ALU instruction.")
        elif tb.type == 'literal':
            lit = 1
            offs = 3
        elif tb.type == 'symbol' and tb.value == '[':
            self.gen_adr(self.tok.next())
            self.inst_ldt()
            offs = 0
        else:
            self.error("Invalid ALU instruction.")

        self.write8(0xe0 + 4*self.get_aluregw(ta.value) + offs)
        if lit:
            self.write16(self.get_literal16(tb))





    # Address

    def get_adrarg(self, t):
        return ['b', 'c', 'sp'].index(t.value)

    def gen_adr(self, t):
        if t.value in ['b', 'c', 'sp']:
            t2 = self.tok.next()
            if (not t2) or (t2.value == ']'): # no offset
                self.write8(0x01 + self.get_adrarg(t))
            elif t2.type == 'symbol' and t2.value == '+': # offset
                t3 = self.tok.next()
                if t3.value == 'x':
                    self.write8(0x0a + self.get_adrarg(t))
                elif t3.value == 'y':
                    self.write8(0x0d + self.get_adrarg(t))
                elif t3.value == 'b':
                    if t.value != 'sp':
                        self.error("Bad addressing mode.")
                    self.write8(0x10)
                elif t3.value == 'c':
                    if t.value == 'sp':
                        self.write8(0x11)
                    elif t.value == 'b':
                        self.write8(0x12)
                    else:
                        self.error("Bad addressing mode.")
                else:
                    offset = self.get_literal(t3)
                    if 0 <= offset <= 255:
                        self.write8(0x04 + self.get_adrarg(t))
                        self.write8(offset)
                    elif 0 <= offset <= 65535:
                        self.write8(0x07 + self.get_adrarg(t))
                        self.write16(offset)
                    else:
                        self.error("Offset out of range.")
            else:
                self.error("Bad addressing mode.")
        else: # immediate
            addr = self.get_literal(t)
            self.write8(0x00)
            self.write16(addr)

    def inst_adr(self):
        t = self.tok.next()
        self.gen_adr(t)

    def inst_adra(self):
        self.write8(0x13)



    def inst_brk(self):
        self.write8(0xff)


    # Pseudoinstructions

    def inst_call(self):
        t = self.tok.next()
        call_addr = self.get_literal16(t)
        ret_addr = self.addr + 6
        # push ret_addr (big endian)
        self.write8(0x41)
        self.write8(ret_addr >> 8)
        self.write8(ret_addr & 0xFF)
        # jmp call_addr
        self.write8(0x30)
        self.write16(call_addr)




    # Directives

    def direc_byte(self):
        t = self.tok.next()
        while t is not None:
            if t.type == 'string':
                for char in t.value:
                    self.write8(ord(char))
            else:
                self.write8(self.get_literal8(t))
            t = self.tok.next()

    def direc_word(self):
        t = self.tok.next()
        while t is not None:
            self.write16(self.get_literal16(t))
            t = self.tok.next()        

    def direc_string(self):
        t = self.tok.next()
        length = 0
        output = []

        while t is not None:
            if t.type == 'string':
                length += len(t.value)
                output += [ord(x) for x in t.value]
            else:
                length += 1
                output += [self.get_literal8(t)]
            t = self.tok.next()

        self.write8(length)
        for b in output:
            self.write8(b)



    def assemble(self, src):
        lines = src.split('\n')

        # pass 1
        print("pass 1:")
        self.addr = 0
        self.pass1 = True
        self.parent_label = ''
        for i, line in enumerate(lines):
            self.line_num = i+1
            self.nbytes = 0
            self.asm_line(line)
            self.addr += self.nbytes

        # pass 2
        print("\n\npass 2:")
        self.output = bytearray()
        self.addr = 0
        self.pass1 = False
        self.line_num = 0
        for i, line in enumerate(lines):
            self.line_num = i+1
            print(f"\n{self.addr:04x}\t", end='')
            self.asm_line(line)
            #print()

        return self.output


    def define_label(self, name, value):
        if name[0] == LOCAL_LABEL_CHAR:
            # Local label
            if self.pass1:
                print(f"\nDefining local label {name}")
                name = self.parent_label + '/' + name[1:]
                self.syms[name] = value
        else:
            self.parent_label = name
            if self.pass1:
                print(f"\nDefining global label {name}")
                self.syms[name] = value


    def define_symbol(self, name, value, allow_redefine=False):
        if not allow_redefine:
            if name in self.syms:
                self.error(f"symbol already defined: {name}")

        if name == '*': # PC
            self.addr = value
        else:
            self.syms[name] = value        

    def is_directive(self, direc):
        return isinstance(direc, str) and (direc[0] == '.') and hasattr(self, "direc_" + direc[1:])
    def run_directive(self, direc):
        return getattr(self, "direc_" + direc[1:])()
    def is_instruction(self, inst):
        return isinstance(inst, str) and hasattr(self, "inst_" + inst)
    def run_instruction(self, inst):
        return getattr(self, "inst_" + inst)()

    def asm_line(self, line):
        self.tok = Tokeniser(line)

        token1 = self.tok.next()
        if token1 is None: return

        word1 = token1.value
        if self.is_instruction(word1):  # unlabelled instruction
            self.run_instruction(word1)
            return
        elif self.is_directive(word1):
            self.run_directive(word1)
            return
        
        token2 = self.tok.next()
        if token2 is None:
            # token1 is just a label
            self.define_label(word1, self.addr)
            return
        elif token2.value == '=':
            # symbol definition
            # redefine on pass2
            token3 = self.tok.next()
            value = self.get_literal(token3)
            self.define_symbol(word1, value, allow_redefine=True)
            return

        # we have a labelled instruction or variable
        word2 = token2.value

        # Store symbol/label address
        self.define_label(word1, self.addr)

        if self.is_instruction(word2):
            self.run_instruction(word2)
            return
        elif self.is_directive(word2):
            self.run_directive(word2)
            return
        else:
            self.error(f"invalid instruction: {word2}")
        




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DIP8 assembler")
    parser.add_argument('srcfile')
    parser.add_argument('outfile', nargs='?', default='out.bin')
    parser.add_argument('-l', '--logisim', action="store_true")
    args = parser.parse_args()

    with open(args.srcfile, 'r') as f:
        src = f.read()

    asm = Assembler()
    out = asm.assemble(src)

    import binascii
    print(f"\nSymbols: {asm.syms}")
    print(f"{len(out)} bytes.")

    if args.logisim:
        print("Creating logisim image.")
        with open(args.outfile, 'w') as f:
            f.write("v2.0 raw\n")
            for byte in out:
                f.write("{} ".format(hex(byte)[2:]))

    else:
        with open(args.outfile, 'wb') as f:
            f.write(out)

