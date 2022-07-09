# Internal signal names.
# The register and ALU selection signals (selx, opadd, etc) get multiplexed into
# 3-bit register and ALU selection words

raw_signals = 'next aout pcinc pcwr irwr memrd memwr alwr ahwr ainc regoe regwr twr alu setflags brk'

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
'!setflags',
'!brk'
]

# T0 (fetch) signals
t0 = ['pcinc', 'memrd', 'irwr']




# Shorthand

LoadLiteral     = 'pcinc memrd'

StoreRegister   = 'aout memwr regoe alu opa'    # store register to RAM
ModifyRegister  = 'regoe alu regwr'             # send register through ALU

AddressSPL      = 'regoe selsl alu opa alwr'    # load address register
AddressSPH      = 'regoe selsh alu opa ahwr'

RegisterToT     = 'regoe alu opa twr'           # write register to t
GenerateAL      = 'regoe alu alwr'              # write AL from register <op> t
GenerateAH      = 'regoe alu ahwr'              # write AH from register <op> t

# Instructions
inst = {}


inst[0xff] = '''brk
    brk'''

# address generation

inst[0x00] = f'''adr ADDR
    {LoadLiteral}   alwr
    {LoadLiteral}   ahwr'''

inst[0x01] = f'''adr b
    {GenerateAL} selbl opa
    {GenerateAH} selbh opa'''
inst[0x02] = f'''adr c
    {GenerateAL} selcl opa
    {GenerateAH} selch opa'''
inst[0x03] = f'''adr sp
    {GenerateAL} selsl opa
    {GenerateAH} selsh opa'''

inst[0x04] = f'''adr b + #L
    {LoadLiteral}   twr
    {GenerateAL} opadd selbl
    {GenerateAH} opci  selbh'''
inst[0x05] = f'''adr c + #L
    {LoadLiteral}   twr
    regoe   selcl   alu     opadd   alwr
    regoe   selch   alu     opci    ahwr'''
inst[0x06] = f'''adr sp + #L
    {LoadLiteral}   twr
    regoe   selsl   alu     opadd   alwr
    regoe   selsh   alu     opci    ahwr'''

inst[0x07] = f'''adr b + #LL
    {LoadLiteral}   twr
    regoe   selbl   alu     opadd   alwr
    {LoadLiteral}   twr
    regoe   selbh   alu     opadc   ahwr'''
inst[0x08] = f'''adr c + #LL
    {LoadLiteral}   twr
    regoe   selcl   alu     opadd   alwr
    {LoadLiteral}   twr
    regoe   selch   alu     opadc   ahwr'''
inst[0x09] = f'''adr sp + #LL
    {LoadLiteral}   twr
    regoe   selsl   alu     opadd   alwr
    {LoadLiteral}   twr
    regoe   selsh   alu     opadc   ahwr'''

inst[0x0a] = f'''adr b + x
    {RegisterToT} selx
    regoe   selbl   alu     opadd   alwr
    regoe   selbh   alu     opci    ahwr'''
inst[0x0b] = f'''adr c + x
    {RegisterToT} selx
    regoe   selcl   alu     opadd   alwr
    regoe   selch   alu     opci    ahwr'''
inst[0x0c] = f'''adr sp + x
    {RegisterToT} selx
    regoe   selsl   alu     opadd   alwr
    regoe   selsh   alu     opci    ahwr'''

inst[0x0d] = f'''adr b + y
    {RegisterToT} sely
    regoe   selbl   alu     opadd   alwr
    regoe   selbh   alu     opci    ahwr'''
inst[0x0e] = f'''adr c + y
    {RegisterToT} sely
    regoe   selcl   alu     opadd   alwr
    regoe   selch   alu     opci    ahwr'''
inst[0x0f] = f'''adr sp + y
    {RegisterToT} sely
    regoe   selsl   alu     opadd   alwr
    regoe   selsh   alu     opci    ahwr'''

inst[0x10] = f'''adr sp + b
    {RegisterToT} selsl
    regoe   selbl   alu     opadd   alwr
    {RegisterToT} selsh
    regoe   selbh   alu     opadc   ahwr'''
inst[0x11] = f'''adr sp + c
    {RegisterToT} selsl
    regoe   selcl   alu     opadd   alwr
    {RegisterToT} selsh
    regoe   selch   alu     opadc   ahwr'''
inst[0x12] = f'''adr b + c
    {RegisterToT} selbl
    regoe   selcl   alu     opadd   alwr
    {RegisterToT} selbh
    regoe   selch   alu     opci    ahwr'''

inst[0x13] = '''adra
    aout    memrd   twr     ainc
    aout    memrd   ahwr
    alu     opb     alwr'''



# jump

inst[0x14] = f'''jmp ADDR
    {LoadLiteral} alwr
    {LoadLiteral} ahwr
    aout pcwr'''



# load/store

inst[0x1f] = f'''stl #L
    {LoadLiteral}   twr
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

inst[0x28] = f'''stx     \n      {StoreRegister} selx'''
inst[0x29] = f'''sty     \n      {StoreRegister} sely'''
inst[0x2c] = f'''stbh    \n      {StoreRegister} selbh'''
inst[0x2d] = f'''stbl    \n      {StoreRegister} selbl'''
inst[0x2e] = f'''stch    \n      {StoreRegister} selch'''
inst[0x2f] = f'''stcl    \n      {StoreRegister} selcl'''
inst[0x2a] = f'''stb
    {StoreRegister} selbl ainc
    {StoreRegister} selbh'''
inst[0x2b] = f'''stc
    {StoreRegister} selcl ainc
    {StoreRegister} selch'''



# stack

inst[0x1e] = f'''ret
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    aout    memrd   twr
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    aout    memrd   ahwr
    alu     opb     alwr
    aout pcwr'''

inst[0x30] = f'''push x
    {AddressSPL}
    {AddressSPH}
    {StoreRegister} selx
    {ModifyRegister} selsl opdec
    {ModifyRegister} selsh opcd'''

inst[0x31] = f'''push y
    {AddressSPL}
    {AddressSPH}
    {StoreRegister} sely
    {ModifyRegister} selsl opdec
    {ModifyRegister} selsh opcd'''

inst[0x32] = f'''push b
    {AddressSPL}
    {AddressSPH}
    {StoreRegister} selbh
    {ModifyRegister} selsl opdec alwr
    {ModifyRegister} selsh opcd  ahwr
    {StoreRegister} selbl
    {ModifyRegister} selsl opdec
    {ModifyRegister} selsh opcd'''

inst[0x33] = f'''push c
    {AddressSPL}
    {AddressSPH}
    {StoreRegister} selch
    {ModifyRegister} selsl opdec alwr
    {ModifyRegister} selsh opcd  ahwr
    {StoreRegister} selcl
    {ModifyRegister} selsl opdec
    {ModifyRegister} selsh opcd'''

inst[0x34] = f'''pop x
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {StoreRegister} selx'''

inst[0x35] = f'''pop y
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {StoreRegister} sely'''

inst[0x36] = f'''pop b
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {StoreRegister} selbl
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {StoreRegister} selbh'''

inst[0x37] = f'''pop c
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {StoreRegister} selcl
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {StoreRegister} selch'''

inst[0x38] = f'''push LL
    {LoadLiteral} twr
    {AddressSPL}
    {AddressSPH}
    aout    memwr   alu     opb
    {LoadLiteral} twr
    {ModifyRegister} selsl opdec alwr
    {ModifyRegister} selsh opcd  ahwr
    aout    memwr   alu     opb
    {ModifyRegister} selsl opdec alwr
    {ModifyRegister} selsh opcd  ahwr'''

inst[0x39] = f'''mov sp, b
    regoe   selbl   alu opa twr
    regwr   selsl   alu opb
    regoe   selbh   alu opa twr
    regwr   selsh   alu opb'''
inst[0x3a] = f'''mov sp, c
    regoe   selcl   alu opa twr
    regwr   selsl   alu opb
    regoe   selch   alu opa twr
    regwr   selsh   alu opb'''
inst[0x3b] = f'''mov b, sp
    regoe   selsl   alu opa twr
    regwr   selbl   alu opb
    regoe   selsh   alu opa twr
    regwr   selbh   alu opb'''
inst[0x3c] = f'''mov c, sp
    regoe   selsl   alu opa twr
    regwr   selcl   alu opb
    regoe   selsh   alu opa twr
    regwr   selch   alu opb'''    


# move reg=literal

inst[0x40] = f'''mov bh, #L
    {LoadLiteral}   regwr   selbh'''
inst[0x47] = f'''mov bl, #L
    {LoadLiteral}   regwr   selbl'''
inst[0x4e] = f'''mov ch, #L
    {LoadLiteral}   regwr   selch'''
inst[0x55] = f'''mov cl, #L
    {LoadLiteral}   regwr   selcl'''
inst[0x5c] = f'''mov x, #L
    {LoadLiteral}   regwr   selx'''
inst[0x63] = f'''mov y, #L
    {LoadLiteral}   regwr   sely'''

inst[0x6d] = f'''mov b, #LL
    {LoadLiteral}   regwr   selbl
    {LoadLiteral}   regwr   selbh'''
inst[0x6e] = f'''mov c, #LL
    {LoadLiteral}   regwr   selcl
    {LoadLiteral}   regwr   selch'''

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
inst[0x6a] = f'''mov t, #L       \n      {LoadLiteral}   twr'''



# arithmetic

inst[0x70] = f'''add x, t        \n      {ModifyRegister} selx  opadd   setflags'''
inst[0x72] = f'''add y, t        \n      {ModifyRegister} sely  opadd   setflags'''
inst[0x74] = f'''add bh, t       \n      {ModifyRegister} selbh opadd   setflags'''
inst[0x76] = f'''add bl, t       \n      {ModifyRegister} selbl opadd   setflags'''
inst[0x78] = f'''add ch, t       \n      {ModifyRegister} selch opadd   setflags'''
inst[0x7a] = f'''add cl, t       \n      {ModifyRegister} selcl opadd   setflags'''
inst[0x71] = f'''add x, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} selx  opadd   setflags'''
inst[0x73] = f'''add y, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} sely  opadd   setflags'''
inst[0x75] = f'''add bh, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbh opadd   setflags'''
inst[0x77] = f'''add bl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbl opadd   setflags'''
inst[0x79] = f'''add ch, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selch opadd   setflags'''
inst[0x7b] = f'''add cl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selcl opadd   setflags'''

inst[0x80] = f'''sub x, t        \n      {ModifyRegister} selx  opsub   setflags'''
inst[0x82] = f'''sub y, t        \n      {ModifyRegister} sely  opsub   setflags'''
inst[0x84] = f'''sub bh, t       \n      {ModifyRegister} selbh opsub   setflags'''
inst[0x86] = f'''sub bl, t       \n      {ModifyRegister} selbl opsub   setflags'''
inst[0x88] = f'''sub ch, t       \n      {ModifyRegister} selch opsub   setflags'''
inst[0x8a] = f'''sub cl, t       \n      {ModifyRegister} selcl opsub   setflags'''
inst[0x81] = f'''sub x, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} selx  opsub   setflags'''
inst[0x83] = f'''sub y, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} sely  opsub   setflags'''
inst[0x85] = f'''sub bh, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbh opsub   setflags'''
inst[0x87] = f'''sub bl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbl opsub   setflags'''
inst[0x89] = f'''sub ch, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selch opsub   setflags'''
inst[0x8b] = f'''sub cl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selcl opsub   setflags'''

