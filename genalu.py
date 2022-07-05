# Generates ROM image for a 4-bit ALU

from pprint import pprint
import binascii

inbits = 16
C = 0
Z = 1
V = 2
K = 3 #clock flags


# add 
def opadd(a, b, c):
    r = a + b
    q = r % 16
    return (q, {C:r>15, K:1})

def opadc(a, b, c):
    r = a + b + c
    q = r % 16
    return (q, {C:r>15, K:1})


# subtract
def opsub(a, b, c):
    r = a + ~b + 1
    cout = a >= b
    q = r % 16
    return (q, {C:cout, K:1})

def opsbc(a, b, c):
    r = a + ~b + c
    cout = (a >= b)    
    q = r % 16
    return (q, {C:cout, K:1})


# logic
def opand(a, b, c):
    q = a & b
    return (q, {C:0, K:0})

def opor(a, b, c):
    q = a | b
    return (q, {C:0, K:0})

def opxor(a, b, c):
    q = a ^ b
    return (q, {C:0, K:0})


# pass-through
def opa(a, b, c):
    return (a, {C:0, K:0})

def opb(a, b, c):
    return (b, {C:0, K:0})


#inc/dec a
def opinc(a, b, c):
    r = a + 1
    q = r % 16
    return (q, {C: r>15, K:1})

def opdec(a, b, c):
    r = a - 1
    cout = a >= 1
    q = r % 16
    return (q, {C: cout, K:1})

# increment if carry
def opci(a, b, c):
    r = a + c
    q = r % 16
    return (q, {C: r>15, K:1})

# decrement if carry
def opcd(a, b, c):
    r = a - c
    cout = a >= c
    q = r % 16
    return (q, {C: cout, K:1})




ops = [
opa,        #0
opb,        #1
opadd,      #2
opsub,      #3
opadc,      #4
opsbc,      #5
opand,      #6
opor,       #7
opxor,      #8
opci,       #9
opinc,      #10
opdec,      #11
opcd        #12
]

print(f"{len(ops)} operators defined")

def create_address(a, b, opsel, user, cu, ci):
    return (a << 0) | (b << 4) | (user << 8) | (opsel << 9) | (ci << 13) | (cu << 14)

def create_data(q, cout, clken):
    z = q == 0
    n = q > 7
    return q | (cout << 4) | (z << 5) | (n << 6) | (clken << 7)

def create_logisim_file(filename, rom):
    with open(filename, 'w') as f:
        f.write("v2.0 raw\n")
        for word in rom:
            f.write("{} ".format(hex(word)[2:]))


def main():
    rom = [0] * 2**inbits

    for user in range(2):
        for cu in range(2):
            for ci in range(2):

                for opnum,op in enumerate(ops):
                    for a in range(16):
                        for b in range(16):

                            # USER pin selects user carry (Cu) vs internal carry (Ci)
                            carryin = cu if user else ci
                            q, flags = op(a,b,carryin)

                            if not user: flags[K] = 0

                            addr = create_address(a, b, opnum, user, cu, ci)
                            data = create_data(q, flags[C], flags[K])
                            rom[addr] = data

    create_logisim_file("alu.rom", rom)


main()



    
        


