# Generates ROM image for a 4-bit ALU

from pprint import pprint
import binascii

address_bits = 16


class Flags():
    def __init__(self, set, C, Z, N):
        self.setflags = set
        self.C = C
        self.Z = Z
        self.N = N


class ALU():
    def __init__(self, lo):
        self.lo = lo
        self.flags = None
        self.nsetflags = 0

    def setflags(self, set=False, C=0, Z=-1, N=-1):
        self.flags = Flags(set, C, Z, N)




    # pass-through
    def opa(self, a, b, c):
        q = a
        self.setflags(False)
        return q

    def opb(self, a, b, c):
        q = b
        self.setflags(False)
        return q

    # add 
    def opadd(self, a, b, c):
        # For add (without carry), first carry in is set to zero
        if self.lo: c = 0

        r = a + b + c
        q = r % 16
        self.setflags(True, C=r>15)
        return q

    def opadc(self, a, b, c):
        r = a + b + c
        q = r % 16
        self.setflags(True, C=r>15)
        return q


    # subtract
    def opsub(self, a, b, c):
        # Force carry=1 (no borrow)
        if self.lo: c = 1

        # For this op, if setflags is not asserted (nsetflags high), 
        # we should do a signed comparison.
        # This means inverting the MSBs of each input before subtracting.
        if self.nsetflags and not self.lo:
            a ^= 0b1000
            b ^= 0b1000

        # We still want to set the flags though, so act as if setflags was asserted
        self.nsetflags = 0


        r = a + ~b + c
        cout = (r >= 0)
        q = r % 16
        self.setflags(True, C=cout)
        return q

    def opsbc(self, a, b, c):
        r = a + ~b + c
        cout = (r >= 0)
        q = r % 16
        self.setflags(True, C=cout)
        return q


    # logic
    def opand(self, a, b, c):
        q = a & b
        self.setflags(True, C=0)
        return q

    def opor(self, a, b, c):
        q = a | b
        self.setflags(True, C=0)
        return q

    def opxor(self, a, b, c):
        q = a ^ b
        self.setflags(True, C=0)
        return q


    #inc/dec a
    def opinc(self, a, b, c):
        if self.lo: c = 1

        r = a + c
        q = r % 16
        self.setflags(True, C=r>15)
        return q

    def opdec(self, a, b, c):
        if self.lo: c = 0

        r = a + ~0 + c
        cout = r >= 0
        q = r % 16
        self.setflags(True, C=cout)
        return q

    # increment if carry set
    def opci(self, a, b, c):
        r = a + c
        q = r % 16
        self.setflags(True, C=r>15)
        return q

    # decrement if carry clear
    def opcd(self, a, b, c):
        r = a + ~0 + c
        cout = r >= 0
        q = r % 16
        self.setflags(True, C=cout)
        return q


    # rotate right
    # takes two operations:

    # input     7654 3210  C <- carry in
    # ror1      0765 C321  4
    # ror2      C765 4321  0 -> carry out = bit 0 of input

    def opror1(self, a, b, c):
        cout = a & 0x01
        q = c<<3 | a>>1
        self.setflags(True, C=cout)
        return q

    def opror2(self, a, b, c):
        cout = a>>3
        q = c<<3 | (a & 0x07)
        self.setflags(True, C=cout)
        return q


    # Set Z=1, N=1
    def opsig(self, a, b, c):
        self.setflags(True, C=0, Z=1, N=1)
        return 0







ops = [
'opa',        #0
'opb',        #1
'opadd',      #2
'opsub',      #3
'opadc',      #4
'opsbc',      #5
'opand',      #6
'opor',       #7
'opxor',      #8
'opci',       #9
'opinc',      #10
'opdec',      #11
'opcd',       #12
'opror1',     #13
'opror2',     #14
'opsig',      #15
]

print(f"{len(ops)} operators defined")

def create_address(a, b, opsel, user, cu, ci, highsel):
    return (a << 0) | (b << 4) | (user << 8) | (opsel << 9) | (ci << 13) | (cu << 14) | (highsel << 15)

def create_data(q, flags, clken):
    c = bool(flags.C)
    z = (q == 0) if flags.Z == -1 else flags.Z
    n = bool(q & 8) if flags.N == -1 else flags.N
    clken = not bool(clken)
    return q | (c << 4) | (z << 5) | (n << 6) | (clken << 7)

def create_logisim_file(filename, rom):
    with open(filename, 'w') as f:
        f.write("v2.0 raw\n")
        for word in rom:
            f.write("{} ".format(hex(word)[2:]))


def main():
    rom = [0] * 2**address_bits

    for highsel in range(2):

        alu = ALU(lo = not highsel)

        for nsetflags in range(2):
            for cu in range(2):
                for ci in range(2):

                    for opnum,op in enumerate(ops):
                        for a in range(16):
                            for b in range(16):

                                # nSETFLAGS pin selects user carry (Cu) vs internal carry (Ci)
                                carryin = ci if nsetflags else cu
                                alu.nsetflags = nsetflags

                                q = getattr(alu, op)(a,b,carryin)
                                flags = alu.flags

                                # upper IC outputs clk enable for user flags
                                # lower IC outputs clk enable for internal carry
                                # No flags are set if the opcode does not set them
                                if highsel:
                                    clken = flags.setflags & ~alu.nsetflags
                                else:
                                    clken = flags.setflags & alu.nsetflags

                                addr = create_address(a, b, opnum, nsetflags, cu, ci, highsel)
                                data = create_data(q, flags, clken)
                                rom[addr] = data

    create_logisim_file("alu.rom", rom)

    byte = bytearray([word for word in rom])
    with open('alu.bin', 'wb') as f:
        f.write(byte)


main()



    
        


