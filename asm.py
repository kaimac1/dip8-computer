#!/bin/python3
import argparse
import sys
import string

ANSI_RED = '\x1b[31m'
ANSI_GREEN = '\x1b[92m'
ANSI_RESET = '\x1b[0m'

addrregs = ['b', 'c']

class Token():
    def __init__(self, toktype, value):
        self.type = toktype
        self.value = value

    def __repr__(self):
        return f"{self.type}({repr(self.value)})"

SYMBOLS = '+'

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
        sys.exit()

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
        sys.exit()

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

    def get_literal(self, t):
        try:
            return int(t.value)
        except:
            name = t.value
            if name in self.syms:
                return self.syms[name]
            else:
                if self.pass1: # don't complain on pass1 if the symbol is not defined yet
                    return 0
                self.error(f"Undefined symbol: {name}")

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
        return ['a','b','c','x','y','z'].index(t.value)

    def inst_push(self):
        t = self.tok.next()
        if is_literal(t):
            self.write8(0x20)
            self.write16(self.get_literal16(t))
        else:
            self.write8(0x21 + self.get_pushpopreg(t))

    def inst_pop(self):
        t = self.tok.next()
        self.write8(0x27 + self.get_pushpopreg(t))



    # Branch

    def jump_common(self, base):
        t = self.tok.next()
        if self.is_address_reg(t):
            self.write8(base + 1 + self.get_address_reg(t))
        else:
            self.write8(base)
            self.write16(self.get_literal16(t))

    def inst_jmp(self):
        self.jump_common(0x30)
    def inst_jcs(self):
        self.jump_common(0x33)
    def inst_jcc(self):
        self.jump_common(0x36)
    def inst_jnz(self):
        self.jump_common(0x39)
    def inst_jz(self):
        self.jump_common(0x3c)

    def inst_ret(self):
        self.write8(0x3f)



    # Address regs

    def ldbc_common(self, base):
        t = self.tok.next()
        if is_literal(t):
            self.write8(base)
            self.write16(self.get_literal16(t))
        else:
            self.write8(base + 1 + self.get_address_reg(t))

    def inst_ldb(self):
        self.ldbc_common(0x40)
    def inst_ldc(self):
        self.ldbc_common(0x44)

    def inst_stb(self):
        t = self.tok.next()
        if t.value == 'c':
            self.write8(0x43)
        else:
            self.error("stb operand must be c")

    def inst_stc(self):
        t = self.tok.next()
        if t.value == 'b':
            self.write8(0x47)
        else:
            self.error("stc operand must be b")

    def inst_inc(self):
        t = self.tok.next()
        idx = ['bh', 'bl', 'ch', 'cl'].index(t.value)
        self.write8(0x48 + idx)

    def inst_dec(self):
        t = self.tok.next()
        idx = ['bh', 'bl', 'ch', 'cl'].index(t.value)
        self.write8(0x4c + idx)



    # Move

    def get_movreg(self, reg):
        return ['a', 'bh', 'bl', 'ch', 'cl', 'x', 'y', 'z'].index(reg)

    def movt_literal(self, t):
        self.write8(0x98)
        self.write8(self.get_literal8(t))
    def movt_register(self, t):
        offset = self.get_movreg(t.value)
        self.write8(0x90 + offset)

    def inst_mov(self):
        ta = self.tok.next()
        tb = self.tok.next()

        if ta is None or tb is None:
            self.error("mov requires two operands")
        if ta.value == tb.value:
            self.error(f"invalid mov instruction")

        if ta.value == 't':
            if tb.type == 'literal':
                self.movt_literal(tb)
            else:
                self.movt_register(tb)
        else:
            dest = self.get_movreg(ta.value)
            if tb.type == 'literal':
                src = self.get_movreg(ta.value)
                self.write8(0x50 + 0x08*dest + src)
                self.write8(self.get_literal8(tb))
            else:
                src = self.get_movreg(tb.value)
                self.write8(0x50 + 0x08*dest + src)


    
    # ALU

    def get_alureg(self, reg):
        return ['a', 'bh', 'bl', 'ch', 'cl', 'x', 'y', 'z'].index(reg)

    def alu_common(self, base):
        ta = self.tok.next()
        tb = self.tok.next()
        if ta is None or tb is None:
            self.error("ALU instructions require two operands.")

        # accept 
        # alu reg, t
        # alu reg, #literal     -> mov t, #literal; alu reg, t
        # alu reg, reg2         -> mov t, reg2;     alu reg, t
        if tb.type == 'literal':
            self.movt_literal(tb)
        elif tb.type == 'text':
            if tb.value != 't':
                self.movt_register(tb)
        else:
            self.error("Invalid ALU instruction.")

        self.write8(base + self.get_alureg(ta.value))

    def inst_add(self):
        self.alu_common(0xa0)
    def inst_sub(self):
        self.alu_common(0xa8)
    def inst_adc(self):
        self.alu_common(0xb0)
    def inst_sbc(self):
        self.alu_common(0xb8)
    def inst_and(self):
        self.alu_common(0xc0)
    def inst_or(self):
        self.alu_common(0xc8)
    def inst_xor(self):
        self.alu_common(0xd0)
    def inst_cmp(self):
        self.alu_common(0xd8)



    # Load/store

    def is_pointer(self, t):
        return t.type == 'text' and t.value[0] == "*"
    def get_pointer(self, t):
        name = t.value[1:]
        if name in self.syms:
            return self.syms[name] & 0xFFFF
        else:
            self.error(f"Undefined symbol: {name}")        


    def is_address_reg_plus_t(self):
        t = self.tok.next()
        if t and t.type == 'symbol' and t.value == '+':
            t2 = self.tok.next()
            return t2.type == 'text' and t2.value == 't'

    def load_common(self, base):
        t = self.tok.next()
        if self.is_pointer(t):
            self.write8(base + 0x01)
            self.write16(self.get_pointer(t))
        elif self.is_address_reg(t):
            if self.is_address_reg_plus_t():
                self.write8(base + 0x04 + self.get_address_reg(t))
            else:
                self.write8(base+ 0x02 + self.get_address_reg(t))
        else: # absolute
            self.write8(base + 0x00)
            self.write16(self.get_literal16(t))

    def store_common(self, base):
        t = self.tok.next()
        if self.is_pointer(t):
            self.write8(base + 0x01)
            self.write16(self.get_pointer(t))
        elif self.is_address_reg(t):
            if self.is_address_reg_plus_t():
                self.write8(base + 0x04 + self.get_address_reg(t))
            else:
                self.write8(base+ 0x02 + self.get_address_reg(t))
        else: # absolute
            self.write8(base + 0x00)
            self.write16(self.get_literal16(t))

    def inst_lda(self):
        self.load_common(0x00)
    def inst_ldz(self):
        self.load_common(0x06)
    def inst_sta(self):
        self.store_common(0x10)
    def inst_stz(self):
        self.store_common(0x16)



    # Pseudoinstructions

    def inst_call(self):
        t = self.tok.next()
        call_addr = self.get_literal16(t)
        ret_addr = self.addr + 6
        # push ret_addr
        self.write8(0x20)
        self.write16(ret_addr)
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
                output += self.get_literal8(t)
            t = self.tok.next()

        self.write16(length)
        for b in output:
            self.write8(b)



    def assemble(self, src):
        lines = src.split('\n')

        # pass 1
        print("pass 1:")
        self.addr = 0
        self.pass1 = True
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
            if self.pass1:
                self.define_symbol(word1, self.addr)
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
        if self.pass1:
            self.define_symbol(word1, self.addr)

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

