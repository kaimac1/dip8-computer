# Generates ROM image for a 4-bit ALU

from pprint import pprint
import binascii

inbits = 16
C = 0
K = 1 #clock flags



class ALU():
    def __init__(self, lo):
        self.lo = lo

    # pass-through
    def opa(self, a, b, c):
        return (a, {C:0, K:0})

    def opb(self, a, b, c):
        return (b, {C:0, K:0})        

    # add 
    def opadd(self, a, b, c):
        # For add (without carry), first carry in is set to zero
        if self.lo: c = 0

        r = a + b + c
        q = r % 16
        return (q, {C:r>15, K:1})

    def opadc(self, a, b, c):
        r = a + b + c
        q = r % 16
        return (q, {C:r>15, K:1})


    # subtract
    def opsub(self, a, b, c):
        # Force carry=1 (no borrow)
        if self.lo: c = 1

        r = a + ~b + c
        cout = (r >= 0)
        q = r % 16
        return (q, {C:cout, K:1})

    def opsbc(self, a, b, c):
        r = a + ~b + c
        cout = (r >= 0)
        q = r % 16
        return (q, {C:cout, K:1})


    # logic
    def opand(self, a, b, c):
        q = a & b
        return (q, {C:0, K:1})

    def opor(self, a, b, c):
        q = a | b
        return (q, {C:0, K:1})

    def opxor(self, a, b, c):
        q = a ^ b
        return (q, {C:0, K:1})


    #inc/dec a
    def opinc(self, a, b, c):
        if self.lo: c = 1

        r = a + c
        q = r % 16
        return (q, {C: r>15, K:1})

    def opdec(self, a, b, c):
        if self.lo: c = 0

        r = a + ~0 + c
        cout = r >= 0
        q = r % 16
        return (q, {C: cout, K:1})

    # increment if carry set
    def opci(self, a, b, c):
        r = a + c
        q = r % 16
        return (q, {C: r>15, K:0})

    # decrement if carry clear
    def opcd(self, a, b, c):
        r = a + ~0 + c
        cout = r >= 0
        q = r % 16
        return (q, {C: cout, K:0})


    # shift
    def opshl(self, a, b, c):
        if self.lo: c = 0

        r = (a << 1) | c
        q = r & 0xF
        return (q, {C: r>15, K:1})






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
'opshl'       #13
]

print(f"{len(ops)} operators defined")

def create_address(a, b, opsel, user, cu, ci, highsel):
    return (a << 0) | (b << 4) | (user << 8) | (opsel << 9) | (ci << 13) | (cu << 14) | (highsel << 15)

def create_data(q, cout, clken):
    z = q == 0
    n = q > 7
    clken = not bool(clken)
    return q | (cout << 4) | (z << 5) | (n << 6) | (clken << 7)

def create_logisim_file(filename, rom):
    with open(filename, 'w') as f:
        f.write("v2.0 raw\n")
        for word in rom:
            f.write("{} ".format(hex(word)[2:]))


def main():
    rom = [0] * 2**inbits

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

                                q, flags = getattr(alu, op)(a,b,carryin)

                                # upper IC outputs clk enable for user flags
                                # lower IC outputs clk enable for internal carry
                                # No flags are set if the opcode does not set them (K=0)
                                if highsel:
                                    clken = flags[K] & ~nsetflags
                                else:
                                    clken = flags[K] & nsetflags

                                addr = create_address(a, b, opnum, nsetflags, cu, ci, highsel)
                                data = create_data(q, flags[C], clken)
                                rom[addr] = data

    create_logisim_file("alu.rom", rom)


main()



    
        


