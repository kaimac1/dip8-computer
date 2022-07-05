# Internal signal names.
# The register and ALU selection signals (selx, opadd, etc) get multiplexed into
# 3-bit register and ALU selection words

raw_signals = 'next aout pcinc pcwr irwr memrd memwr alwr ahwr ainc regoe regwr twr alu aluint'

regsel = ['selbh', 'selbl', 'selch', 'selcl', 'selx', 'sely', 'selsh', 'selsl']
alusel = ['opa', 'opb', 'opadd', 'opsub', 'opadc', 'opsbc', 'opand', 'opor', 'opxor', 'opci', 'opinc', 'opdec', 'opcd']

raw_signals = raw_signals.split(" ")
raw_signals.extend(regsel)
raw_signals.extend(alusel)

# Output signals, listed in the correct order (LSB->MSB)
# ! denotes that the signal is inverted.

output_signals = [
'!next',
'aout',
'!pcinc',
'!pcwr',
'irwr',
'!memrd',
'!memwr',
'opsel0',
'opsel1',
'opsel2',
'opsel3',
'regsel0',
'regsel1',
'regsel2',
'!ahwr',
'!alwr',
'!regoe',
'!regwr',
'!ainc',
'!alu',
'twr',
'!aluint'
]

t0 = ['pcinc', 'memrd', 'irwr']


# Instructions
inst = {}

# the t0 fetch signals above are not added automatically to the halt instruction,
# so it never fetches the next instruction.
inst[0xff] = '''halt
    '''


# address generation

inst[0x00] = '''adr ADDR
    pcinc   memrd   alwr
    pcinc   memrd   ahwr'''

inst[0x01] = '''adr b
    regoe   selbl   alu     alwr
    regoe   selbh   alu     ahwr'''
inst[0x02] = '''adr c
    regoe   selcl   alu     alwr
    regoe   selch   alu     ahwr'''
inst[0x03] = '''adr sp
    regoe   selsl   alu     alwr
    regoe   selsh   alu     ahwr'''

inst[0x04] = '''adr b + #L
    pcinc   memrd   twr
    regoe   selbl   alu     aluint  opadd   alwr
    regoe   selbh   alu     aluint  opci    ahwr'''
inst[0x05] = '''adr c + #L
    pcinc   memrd   twr
    regoe   selcl   alu     aluint  opadd   alwr
    regoe   selch   alu     aluint  opci    ahwr'''
inst[0x06] = '''adr sp + #L
    pcinc   memrd   twr
    regoe   selsl   alu     aluint  opadd   alwr
    regoe   selsh   alu     aluint  opci    ahwr'''

inst[0x07] = '''adr b + #LL
    pcinc   memrd   twr
    regoe   selbl   alu     aluint  opadd   alwr
    pcinc   memrd   twr
    regoe   selbh   alu     aluint  opadc   ahwr'''
inst[0x08] = '''adr c + #LL
    pcinc   memrd   twr
    regoe   selcl   alu     opadd   alwr
    pcinc   memrd   twr
    regoe   selch   alu     opadc    ahwr'''
inst[0x09] = '''adr sp + #LL
    pcinc   memrd   twr
    regoe   selsl   alu     opadd   alwr
    pcinc   memrd   twr
    regoe   selsh   alu     opadc   ahwr'''

inst[0x0a] = '''adr b + x
    regoe   selx    alu     opa     twr
    regoe   selbl   alu     opadd   alwr
    regoe   selbh   alu     opci    ahwr'''
inst[0x0b] = '''adr c + x
    regoe   selx    alu     opa     twr
    regoe   selcl   alu     opadd   alwr
    regoe   selch   alu     opci    ahwr'''
inst[0x0c] = '''adr sp + x
    regoe   selx    alu     opa     twr
    regoe   selsl   alu     opadd   alwr
    regoe   selsh   alu     opci    ahwr'''

inst[0x0d] = '''adr b + y
    regoe   sely    alu     opa     twr
    regoe   selbl   alu     opadd   alwr
    regoe   selbh   alu     opci    ahwr'''
inst[0x0e] = '''adr c + y
    regoe   sely    alu     opa     twr
    regoe   selcl   alu     opadd   alwr
    regoe   selch   alu     opci    ahwr'''
inst[0x0f] = '''adr sp + y
    regoe   sely    alu     opa     twr
    regoe   selsl   alu     opadd   alwr
    regoe   selsh   alu     opci    ahwr'''

inst[0x10] = '''adr sp + b
    regoe   selsl   alu     opa     twr
    regoe   selbl   alu     opadd   alwr
    regoe   selsh   alu     opa     twr
    regoe   selbh   alu     opadc   ahwr'''
inst[0x11] = '''adr sp + c
    regoe   selsl   alu     opa     twr
    regoe   selcl   alu     opadd   alwr
    regoe   selsh   alu     opa     twr
    regoe   selch   alu     opadc   ahwr'''
inst[0x12] = '''adr b + c
    regoe   selbl   alu     opa     twr
    regoe   selcl   alu     opadd   alwr
    regoe   selbh   alu     opa     twr
    regoe   selch   alu     opci    ahwr'''

inst[0x13] = '''adra
    aout    memrd   twr     ainc
    aout    memrd   ahwr
    alu     opb     alwr'''

# jump

# load/store

inst[0x1f] = '''stl #L
    pcinc   memrd   twr
    aout    memwr   alu     opb'''

inst[0x20] = '''ldx     \n      aout    memrd   regwr   selx'''
inst[0x21] = '''ldy     \n      aout    memrd   regwr   sely'''
inst[0x24] = '''ldbh    \n      aout    memrd   regwr   selbh'''
inst[0x25] = '''ldbl    \n      aout    memrd   regwr   selbl'''
inst[0x26] = '''ldch    \n      aout    memrd   regwr   selch'''
inst[0x27] = '''ldcl    \n      aout    memrd   regwr   selcl'''
inst[0x22] = '''ldb
    aout    memrd   regwr   selbl   ainc
    aout    memrd   regwr   selbh'''
inst[0x23] = '''ldc
    aout    memrd   regwr   selcl   ainc
    aout    memrd   regwr   selch'''

inst[0x28] = '''stx     \n      aout    memwr   regoe   selx    alu     opa'''
inst[0x29] = '''sty     \n      aout    memwr   regoe   sely    alu     opa'''
inst[0x2c] = '''stbh    \n      aout    memwr   regoe   selbh   alu     opa'''
inst[0x2d] = '''stbl    \n      aout    memwr   regoe   selbl   alu     opa'''
inst[0x2e] = '''stch    \n      aout    memwr   regoe   selch   alu     opa'''
inst[0x2f] = '''stcl    \n      aout    memwr   regoe   selcl   alu     opa'''
inst[0x2a] = '''stb
    aout    memwr   regoe   selbl   alu     opa     ainc
    aout    memwr   regoe   selbh   alu     opa'''
inst[0x2b] = '''stc
    aout    memwr   regoe   selcl   alu     opa     ainc
    aout    memwr   regoe   selch   alu     opa'''

# stack

inst[0x1e] = '''ret
    '''

inst[0x30] = '''push x
    regoe   selsl   alu     opa     alwr
    regoe   selsh   alu     opa     ahwr
    aout    memwr   regoe   selx    opa
    regoe   selsl   alu     opdec   regwr
    regoe   selsh   alu     opcd    regwr'''

inst[0x34] = '''pop x
    regoe   selsl   alu     opinc   alwr    regwr
    regoe   selsh   alu     opci    ahwr    regwr
    aout    memwr   regoe   selx    alu     opa'''


# inst[0x32] = '''push b
#     regoe   selsl   alu     opa     alwr
#     regoe   selsh   alu     opa     ahwr
#     aout    memwr   regoe   selbh   opa
#     regoe   selsl   alu     opdec   regwr   alwr
#     regoe   selsh   alu     opd2    regwr   ahwr
#     aout    memwr   regoe   selbl   opa
#     regoe   selsl   alu     opdec   regwr   alwr
#     regoe   selsh   alu     opd2    regwr   ahwr'''
# inst[0x32] = '''push LL
#     pcinc   memrd   twr
#     regoe   selsl   alu     opa     alwr
#     regoe   selsh   alu     opa     ahwr
#     aout    memwr   alu     opb
#     pcinc   memrd   twr
#     regoe   selsl   alu     opdec   regwr   alwr
#     regoe   selsh   alu     opd2    regwr   ahwr
#     aout    memwr   alu     opb
#     regoe   selsl   alu     opdec   regwr   alwr
#     regoe   selsh   alu     opd2    regwr   ahwr'''

# inst[0x32] = '''pop b
#     regoe   selsl   alu     opinc   alwr    regwr
#     regoe   selsh   alu     opac    ahwr    regwr
#     aout    memwr   regoe   selbh   opa
#     regoe   selsl   alu     opinc   regwr   alwr
#     regoe   selsh   alu     opac    regwr   ahwr
#     aout    memwr   regoe   selbl   opa'''

# inst[] = '''ret
#     regoe   selsl   alu     opinc   alwr    regwr
#     regoe   selsh   alu     opac    alwr    regwr
#     aout    memrd   twr
#     regoe   selsl   alu     opinc   alwr    regwr
#     regoe   selsh   alu     opac    alwr    regwr
#     aout    memrd   ahwr
#     alu     opb     alwr
#     aout pcwr
# '''




# move reg=literal

inst[0x40] = '''mov bh, #L
    pcinc   memrd   regwr   selbh'''
inst[0x47] = '''mov bl, #L
    pcinc   memrd   regwr   selbl'''
inst[0x4e] = '''mov ch, #L
    pcinc   memrd   regwr   selch'''
inst[0x55] = '''mov cl, #L
    pcinc   memrd   regwr   selcl'''
inst[0x5c] = '''mov x, #L
    pcinc   memrd   regwr   selx'''
inst[0x63] = '''mov y, #L
    pcinc   memrd   regwr   sely'''

inst[0x6d] = '''mov b, #LL
    pcinc   memrd   regwr   selbl
    pcinc   memrd   regwr   selbh'''
inst[0x6e] = '''mov c, #LL
    pcinc   memrd   regwr   selcl
    pcinc   memrd   regwr   selch'''

# ldt

inst[0x6f] = '''ldt
    aout    memrd   twr'''

# move reg=reg

inst[0x41] = '''mov bh, bl      \n      regoe   selbl   alu     opa     twr     \n      regwr   selbh   alu     opb'''
inst[0x42] = '''mov bh, ch      \n      regoe   selch   alu     opa     twr     \n      regwr   selbh   alu     opb'''
inst[0x43] = '''mov bh, cl      \n      regoe   selcl   alu     opa     twr     \n      regwr   selbh   alu     opb'''
inst[0x44] = '''mov bh, x       \n      regoe   selx    alu     opa     twr     \n      regwr   selbh   alu     opb'''    
inst[0x45] = '''mov bh, y       \n      regoe   sely    alu     opa     twr     \n      regwr   selbh   alu     opb'''

inst[0x46] = '''mov bl, bh      \n      regoe   selbh   alu     opa     twr     \n      regwr   selbl   alu     opb'''
inst[0x48] = '''mov bl, ch      \n      regoe   selch   alu     opa     twr     \n      regwr   selbl   alu     opb'''
inst[0x49] = '''mov bl, cl      \n      regoe   selcl   alu     opa     twr     \n      regwr   selbl   alu     opb'''
inst[0x4a] = '''mov bl, x       \n      regoe   selx    alu     opa     twr     \n      regwr   selbl   alu     opb'''
inst[0x4b] = '''mov bl, y       \n      regoe   sely    alu     opa     twr     \n      regwr   selbl   alu     opb'''

inst[0x4c] = '''mov ch, bh      \n      regoe   selbh   alu     opa     twr     \n      regwr   selch   alu     opb'''
inst[0x4d] = '''mov ch, bl      \n      regoe   selbl   alu     opa     twr     \n      regwr   selch   alu     opb'''
inst[0x4f] = '''mov ch, cl      \n      regoe   selcl   alu     opa     twr     \n      regwr   selch   alu     opb'''
inst[0x50] = '''mov ch, x       \n      regoe   selx    alu     opa     twr     \n      regwr   selch   alu     opb'''
inst[0x51] = '''mov ch, y       \n      regoe   sely    alu     opa     twr     \n      regwr   selch   alu     opb'''

inst[0x52] = '''mov cl, bh      \n      regoe   selbh   alu     opa     twr     \n      regwr   selcl   alu     opb'''
inst[0x53] = '''mov cl, bl      \n      regoe   selbl   alu     opa     twr     \n      regwr   selcl   alu     opb'''
inst[0x54] = '''mov cl, ch      \n      regoe   selch   alu     opa     twr     \n      regwr   selcl   alu     opb'''
inst[0x56] = '''mov cl, x       \n      regoe   selx    alu     opa     twr     \n      regwr   selcl   alu     opb'''
inst[0x57] = '''mov cl, y       \n      regoe   sely    alu     opa     twr     \n      regwr   selcl   alu     opb'''

inst[0x58] = '''mov x, bh       \n      regoe   selbh   alu     opa     twr     \n      regwr   selx    alu     opb'''
inst[0x59] = '''mov x, bl       \n      regoe   selbl   alu     opa     twr     \n      regwr   selx    alu     opb'''
inst[0x5a] = '''mov x, ch       \n      regoe   selch   alu     opa     twr     \n      regwr   selx    alu     opb'''
inst[0x5b] = '''mov x, cl       \n      regoe   selcl   alu     opa     twr     \n      regwr   selx    alu     opb'''
inst[0x5d] = '''mov x, y        \n      regoe   sely    alu     opa     twr     \n      regwr   selx    alu     opb'''

inst[0x5e] = '''mov y, bh       \n      regoe   selbh   alu     opa     twr     \n      regwr   sely    alu     opb'''
inst[0x5f] = '''mov y, bl       \n      regoe   selbl   alu     opa     twr     \n      regwr   sely    alu     opb'''
inst[0x60] = '''mov y, ch       \n      regoe   selch   alu     opa     twr     \n      regwr   sely    alu     opb'''
inst[0x61] = '''mov y, cl       \n      regoe   selcl   alu     opa     twr     \n      regwr   sely    alu     opb'''
inst[0x62] = '''mov y, x        \n      regoe   selx    alu     opa     twr     \n      regwr   sely    alu     opb'''

# move t=

inst[0x64] = '''mov t, bh       \n      regoe   selbh   alu     opa     twr'''
inst[0x65] = '''mov t, bl       \n      regoe   selbl   alu     opa     twr'''
inst[0x66] = '''mov t, ch       \n      regoe   selch   alu     opa     twr'''
inst[0x67] = '''mov t, cl       \n      regoe   selcl   alu     opa     twr'''
inst[0x68] = '''mov t, x        \n      regoe   selx    alu     opa     twr'''
inst[0x69] = '''mov t, y        \n      regoe   sely    alu     opa     twr'''
inst[0x6a] = '''mov t, #L       \n      pcinc   memrd   twr'''

# arithmetic

inst[0x70] = '''add x, t        \n      regoe   regwr   selx    alu     opadd'''
