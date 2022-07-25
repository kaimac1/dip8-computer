# Internal signal names.
# The register and ALU selection signals (selx, opadd, etc) get multiplexed into
# 3-bit register and ALU selection words

raw_signals = 'next aout pcinc pcwr irwr memrd memwr alwr ahwr ainc regoe regwr twr alu setflags brk'

regsel = ['selbh', 'selbl', 'selch', 'selcl', 'selx', 'sely', 'selsh', 'selsl']
alusel = ['opa', 'opb', 'opadd', 'opsub', 'opadc', 'opsbc', 'opand', 'opor', 'opxor', 'opci', 'opinc', 'opdec', 'opcd', 'opror1', 'opror2']

raw_signals = raw_signals.split(" ")
raw_signals.extend(regsel)
raw_signals.extend(alusel)

# Output signals, listed in the correct order (LSB->MSB)
# ! denotes that the signal is inverted.

output_signals = [
'!next',    # 0
'aout',     # 1
'!pcinc',   # 2
'!pcwr',    # 3
'!irwr',    # 4
'!memrd',   # 5
'!memwr',   # 6
'!ainc',    # 7
'!ahwr',     # 0
'!alwr',     # 1
'!regoe',    # 2
'!regwr',    # 3
'opsel0',    # 4
'opsel1',    # 5
'opsel2',    # 6
'opsel3',    # 7
'regsel0',    # 0
'regsel1',    # 1
'regsel2',    # 2
'!alu',       # 3
'twr',        # 4
'!setflags',  # 5
'!brk'        # 6
]

# T0 (fetch) signals
t0 = ['pcinc', 'memrd', 'irwr']




# Shorthand

LoadLiteral     = 'pcinc memrd'                 # literal -> data bus

LoadRegister    = 'aout memrd regwr'
StoreRegister   = 'aout memwr regoe alu opa'    # store [register] to RAM
ModifyRegister  = 'regoe alu regwr'             # send [register] through ALU [op]

AddressSPL      = 'regoe selsl alu opa alwr'    # load address register
AddressSPH      = 'regoe selsh alu opa ahwr'

RegisterToT     = 'regoe alu opa twr'           # write [register] to t
TToRegister     = 'regwr alu opb'               # write t to [register]
GenerateAL      = 'regoe alu alwr'              # write AL from [register] [op] t
GenerateAH      = 'regoe alu ahwr'              # write AH from [register] [op] t

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
    regoe   selch   alu     opadc   ahwr'''

inst[0x13] = '''adra
    aout    memrd   twr     ainc
    aout    memrd   ahwr
    alu     opb     alwr'''



# jump

inst[0x14] = f'''jmp ADDR
    {LoadLiteral} alwr
    {LoadLiteral} ahwr
    aout pcwr'''
inst[0x15] = f'''jmpa
    aout pcwr'''

inst[0x16] = f'''jcs ADDR
    {LoadLiteral} alwr
    {LoadLiteral} ahwr
    (CS) aout pcwr'''
inst[0x17] = f'''jcsa
    (CS) aout pcwr'''

inst[0x18] = f'''jcc ADDR
    {LoadLiteral} alwr
    {LoadLiteral} ahwr
    (CC) aout pcwr'''
inst[0x19] = f'''jcca
    (CC) aout pcwr'''

inst[0x1a] = f'''jz ADDR
    {LoadLiteral} alwr
    {LoadLiteral} ahwr
    (Z) aout pcwr'''
inst[0x1b] = f'''jza
    (Z) aout pcwr'''    

inst[0x1c] = f'''jnz ADDR
    {LoadLiteral} alwr
    {LoadLiteral} ahwr
    (NZ) aout pcwr'''
inst[0x1d] = f'''jnza
    (NZ) aout pcwr'''

inst[0x1e] = f'''ret
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    aout    memrd   twr
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    aout    memrd   ahwr
    alu     opb     alwr
    aout pcwr'''




# load/store

inst[0x1f] = f'''stl #L
    {LoadLiteral}   twr
    aout    memwr   alu     opb'''

inst[0x20] = f'''ldx     \n      {LoadRegister} selx'''
inst[0x21] = f'''ldy     \n      {LoadRegister} sely'''
inst[0x24] = f'''ldbh    \n      {LoadRegister} selbh'''
inst[0x25] = f'''ldbl    \n      {LoadRegister} selbl'''
inst[0x26] = f'''ldch    \n      {LoadRegister} selch'''
inst[0x27] = f'''ldcl    \n      {LoadRegister} selcl'''
inst[0x22] = f'''ldb
    {LoadRegister} selbl
    ainc
    {LoadRegister} selbh'''
inst[0x23] = f'''ldc
    {LoadRegister} selcl
    ainc
    {LoadRegister} selch'''

inst[0x28] = f'''stx     \n      {StoreRegister} selx'''
inst[0x29] = f'''sty     \n      {StoreRegister} sely'''
inst[0x2c] = f'''stbh    \n      {StoreRegister} selbh'''
inst[0x2d] = f'''stbl    \n      {StoreRegister} selbl'''
inst[0x2e] = f'''stch    \n      {StoreRegister} selch'''
inst[0x2f] = f'''stcl    \n      {StoreRegister} selcl'''
inst[0x2a] = f'''stb
    {StoreRegister} selbl
    ainc
    {StoreRegister} selbh'''
inst[0x2b] = f'''stc
    {StoreRegister} selcl
    ainc
    {StoreRegister} selch'''



# stack

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
    {LoadRegister} selx'''

inst[0x35] = f'''pop y
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {LoadRegister} sely'''

inst[0x36] = f'''pop b
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {LoadRegister} selbl
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {LoadRegister} selbh'''

inst[0x37] = f'''pop c
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {LoadRegister} selcl
    {ModifyRegister} selsl opinc alwr
    {ModifyRegister} selsh opci  ahwr
    {LoadRegister} selch'''

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

inst[0x41] = f'''mov bh, bl      \n      {RegisterToT}   selbl     \n      {TToRegister}   selbh'''
inst[0x42] = f'''mov bh, ch      \n      {RegisterToT}   selch     \n      {TToRegister}   selbh'''
inst[0x43] = f'''mov bh, cl      \n      {RegisterToT}   selcl     \n      {TToRegister}   selbh'''
inst[0x44] = f'''mov bh, x       \n      {RegisterToT}   selx      \n      {TToRegister}   selbh'''    
inst[0x45] = f'''mov bh, y       \n      {RegisterToT}   sely      \n      {TToRegister}   selbh'''

inst[0x46] = f'''mov bl, bh      \n      {RegisterToT}   selbh     \n      {TToRegister}   selbl'''
inst[0x48] = f'''mov bl, ch      \n      {RegisterToT}   selch     \n      {TToRegister}   selbl'''
inst[0x49] = f'''mov bl, cl      \n      {RegisterToT}   selcl     \n      {TToRegister}   selbl'''
inst[0x4a] = f'''mov bl, x       \n      {RegisterToT}   selx      \n      {TToRegister}   selbl'''
inst[0x4b] = f'''mov bl, y       \n      {RegisterToT}   sely      \n      {TToRegister}   selbl'''

inst[0x4c] = f'''mov ch, bh      \n      {RegisterToT}   selbh     \n      {TToRegister}   selch'''
inst[0x4d] = f'''mov ch, bl      \n      {RegisterToT}   selbl     \n      {TToRegister}   selch'''
inst[0x4f] = f'''mov ch, cl      \n      {RegisterToT}   selcl     \n      {TToRegister}   selch'''
inst[0x50] = f'''mov ch, x       \n      {RegisterToT}   selx      \n      {TToRegister}   selch'''
inst[0x51] = f'''mov ch, y       \n      {RegisterToT}   sely      \n      {TToRegister}   selch'''

inst[0x52] = f'''mov cl, bh      \n      {RegisterToT}   selbh     \n      {TToRegister}   selcl'''
inst[0x53] = f'''mov cl, bl      \n      {RegisterToT}   selbl     \n      {TToRegister}   selcl'''
inst[0x54] = f'''mov cl, ch      \n      {RegisterToT}   selch     \n      {TToRegister}   selcl'''
inst[0x56] = f'''mov cl, x       \n      {RegisterToT}   selx      \n      {TToRegister}   selcl'''
inst[0x57] = f'''mov cl, y       \n      {RegisterToT}   sely      \n      {TToRegister}   selcl'''

inst[0x58] = f'''mov x, bh       \n      {RegisterToT}   selbh     \n      {TToRegister}   selx '''
inst[0x59] = f'''mov x, bl       \n      {RegisterToT}   selbl     \n      {TToRegister}   selx '''
inst[0x5a] = f'''mov x, ch       \n      {RegisterToT}   selch     \n      {TToRegister}   selx '''
inst[0x5b] = f'''mov x, cl       \n      {RegisterToT}   selcl     \n      {TToRegister}   selx '''
inst[0x5d] = f'''mov x, y        \n      {RegisterToT}   sely      \n      {TToRegister}   selx '''

inst[0x5e] = f'''mov y, bh       \n      {RegisterToT}   selbh     \n      {TToRegister}   sely '''
inst[0x5f] = f'''mov y, bl       \n      {RegisterToT}   selbl     \n      {TToRegister}   sely '''
inst[0x60] = f'''mov y, ch       \n      {RegisterToT}   selch     \n      {TToRegister}   sely '''
inst[0x61] = f'''mov y, cl       \n      {RegisterToT}   selcl     \n      {TToRegister}   sely '''
inst[0x62] = f'''mov y, x        \n      {RegisterToT}   selx      \n      {TToRegister}   sely '''

# move t=

inst[0x64] = f'''mov t, bh       \n      {RegisterToT}   selbh'''
inst[0x65] = f'''mov t, bl       \n      {RegisterToT}   selbl'''
inst[0x66] = f'''mov t, ch       \n      {RegisterToT}   selch'''
inst[0x67] = f'''mov t, cl       \n      {RegisterToT}   selcl'''
inst[0x68] = f'''mov t, x        \n      {RegisterToT}   selx '''
inst[0x69] = f'''mov t, y        \n      {RegisterToT}   sely '''
inst[0x6a] = f'''mov t, #L       \n      {LoadLiteral}   twr'''

# move 16 bit

inst[0x6b] = f'''mov b, c
    {RegisterToT} selcl
    {TToRegister} selbl
    {RegisterToT} selch
    {TToRegister} selbh'''
inst[0x6c] = f'''mov c, b
    {RegisterToT} selbl
    {TToRegister} selcl
    {RegisterToT} selbh
    {TToRegister} selch'''



# arithmetic/logic

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

inst[0x7c] = f'''sub x, t        \n      {ModifyRegister} selx  opsub   setflags'''
inst[0x7e] = f'''sub y, t        \n      {ModifyRegister} sely  opsub   setflags'''
inst[0x80] = f'''sub bh, t       \n      {ModifyRegister} selbh opsub   setflags'''
inst[0x82] = f'''sub bl, t       \n      {ModifyRegister} selbl opsub   setflags'''
inst[0x84] = f'''sub ch, t       \n      {ModifyRegister} selch opsub   setflags'''
inst[0x86] = f'''sub cl, t       \n      {ModifyRegister} selcl opsub   setflags'''
inst[0x7d] = f'''sub x, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} selx  opsub   setflags'''
inst[0x7f] = f'''sub y, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} sely  opsub   setflags'''
inst[0x81] = f'''sub bh, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbh opsub   setflags'''
inst[0x83] = f'''sub bl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbl opsub   setflags'''
inst[0x85] = f'''sub ch, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selch opsub   setflags'''
inst[0x87] = f'''sub cl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selcl opsub   setflags'''

inst[0x88] = f'''adc x, t        \n      {ModifyRegister} selx  opadc   setflags'''
inst[0x8a] = f'''adc y, t        \n      {ModifyRegister} sely  opadc   setflags'''
inst[0x8c] = f'''adc bh, t       \n      {ModifyRegister} selbh opadc   setflags'''
inst[0x8e] = f'''adc bl, t       \n      {ModifyRegister} selbl opadc   setflags'''
inst[0x90] = f'''adc ch, t       \n      {ModifyRegister} selch opadc   setflags'''
inst[0x92] = f'''adc cl, t       \n      {ModifyRegister} selcl opadc   setflags'''
inst[0x89] = f'''adc x, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} selx  opadc   setflags'''
inst[0x8b] = f'''adc y, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} sely  opadc   setflags'''
inst[0x8d] = f'''adc bh, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbh opadc   setflags'''
inst[0x8f] = f'''adc bl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbl opadc   setflags'''
inst[0x91] = f'''adc ch, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selch opadc   setflags'''
inst[0x93] = f'''adc cl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selcl opadc   setflags'''

inst[0x94] = f'''sbc x, t        \n      {ModifyRegister} selx  opsbc   setflags'''
inst[0x96] = f'''sbc y, t        \n      {ModifyRegister} sely  opsbc   setflags'''
inst[0x98] = f'''sbc bh, t       \n      {ModifyRegister} selbh opsbc   setflags'''
inst[0x9a] = f'''sbc bl, t       \n      {ModifyRegister} selbl opsbc   setflags'''
inst[0x9c] = f'''sbc ch, t       \n      {ModifyRegister} selch opsbc   setflags'''
inst[0x9e] = f'''sbc cl, t       \n      {ModifyRegister} selcl opsbc   setflags'''
inst[0x95] = f'''sbc x, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} selx  opsbc   setflags'''
inst[0x97] = f'''sbc y, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} sely  opsbc   setflags'''
inst[0x99] = f'''sbc bh, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbh opsbc   setflags'''
inst[0x9b] = f'''sbc bl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbl opsbc   setflags'''
inst[0x9d] = f'''sbc ch, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selch opsbc   setflags'''
inst[0x9f] = f'''sbc cl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selcl opsbc   setflags'''

inst[0xa0] = f'''cmp x, t        \n      regoe alu selx  opsub   setflags'''
inst[0xa2] = f'''cmp y, t        \n      regoe alu sely  opsub   setflags'''
inst[0xa4] = f'''cmp bh, t       \n      regoe alu selbh opsub   setflags'''
inst[0xa6] = f'''cmp bl, t       \n      regoe alu selbl opsub   setflags'''
inst[0xa8] = f'''cmp ch, t       \n      regoe alu selch opsub   setflags'''
inst[0xaa] = f'''cmp cl, t       \n      regoe alu selcl opsub   setflags'''
inst[0xa1] = f'''cmp x, #L       \n      {LoadLiteral} twr      \n      regoe alu selx  opsub   setflags'''
inst[0xa3] = f'''cmp y, #L       \n      {LoadLiteral} twr      \n      regoe alu sely  opsub   setflags'''
inst[0xa5] = f'''cmp bh, #L      \n      {LoadLiteral} twr      \n      regoe alu selbh opsub   setflags'''
inst[0xa7] = f'''cmp bl, #L      \n      {LoadLiteral} twr      \n      regoe alu selbl opsub   setflags'''
inst[0xa9] = f'''cmp ch, #L      \n      {LoadLiteral} twr      \n      regoe alu selch opsub   setflags'''
inst[0xab] = f'''cmp cl, #L      \n      {LoadLiteral} twr      \n      regoe alu selcl opsub   setflags'''

inst[0xac] = f'''and x, t        \n      {ModifyRegister} selx  opand setflags'''
inst[0xae] = f'''and y, t        \n      {ModifyRegister} sely  opand setflags'''
inst[0xb0] = f'''and bh, t       \n      {ModifyRegister} selbh opand setflags'''
inst[0xb2] = f'''and bl, t       \n      {ModifyRegister} selbl opand setflags'''
inst[0xb4] = f'''and ch, t       \n      {ModifyRegister} selch opand setflags'''
inst[0xb6] = f'''and cl, t       \n      {ModifyRegister} selcl opand setflags'''
inst[0xad] = f'''and x, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} selx  opand setflags'''
inst[0xaf] = f'''and y, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} sely  opand setflags'''
inst[0xb1] = f'''and bh, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbh opand setflags'''
inst[0xb3] = f'''and bl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbl opand setflags'''
inst[0xb5] = f'''and ch, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selch opand setflags'''
inst[0xb7] = f'''and cl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selcl opand setflags'''

inst[0xb8] = f'''or x, t        \n      {ModifyRegister} selx  opor setflags'''
inst[0xba] = f'''or y, t        \n      {ModifyRegister} sely  opor setflags'''
inst[0xbc] = f'''or bh, t       \n      {ModifyRegister} selbh opor setflags'''
inst[0xbe] = f'''or bl, t       \n      {ModifyRegister} selbl opor setflags'''
inst[0xc0] = f'''or ch, t       \n      {ModifyRegister} selch opor setflags'''
inst[0xc2] = f'''or cl, t       \n      {ModifyRegister} selcl opor setflags'''
inst[0xb9] = f'''or x, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} selx  opor setflags'''
inst[0xbb] = f'''or y, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} sely  opor setflags'''
inst[0xbd] = f'''or bh, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbh opor setflags'''
inst[0xbf] = f'''or bl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbl opor setflags'''
inst[0xc1] = f'''or ch, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selch opor setflags'''
inst[0xc3] = f'''or cl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selcl opor setflags'''

inst[0xc4] = f'''xor x, t        \n      {ModifyRegister} selx  opxor setflags'''
inst[0xc6] = f'''xor y, t        \n      {ModifyRegister} sely  opxor setflags'''
inst[0xc8] = f'''xor bh, t       \n      {ModifyRegister} selbh opxor setflags'''
inst[0xca] = f'''xor bl, t       \n      {ModifyRegister} selbl opxor setflags'''
inst[0xcc] = f'''xor ch, t       \n      {ModifyRegister} selch opxor setflags'''
inst[0xce] = f'''xor cl, t       \n      {ModifyRegister} selcl opxor setflags'''
inst[0xc5] = f'''xor x, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} selx  opxor setflags'''
inst[0xc7] = f'''xor y, #L       \n      {LoadLiteral} twr      \n      {ModifyRegister} sely  opxor setflags'''
inst[0xc9] = f'''xor bh, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbh opxor setflags'''
inst[0xcb] = f'''xor bl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selbl opxor setflags'''
inst[0xcd] = f'''xor ch, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selch opxor setflags'''
inst[0xcf] = f'''xor cl, #L      \n      {LoadLiteral} twr      \n      {ModifyRegister} selcl opxor setflags'''

inst[0xd0] = f'''ror x           \n      {ModifyRegister} selx  opror1 setflags \n      {ModifyRegister} selx  opror2 setflags'''
inst[0xd1] = f'''ror y           \n      {ModifyRegister} sely  opror1 setflags \n      {ModifyRegister} sely  opror2 setflags'''
inst[0xd2] = f'''ror bh          \n      {ModifyRegister} selbh opror1 setflags \n      {ModifyRegister} selbh opror2 setflags'''
inst[0xd3] = f'''ror bl          \n      {ModifyRegister} selbl opror1 setflags \n      {ModifyRegister} selbl opror2 setflags'''
inst[0xd4] = f'''ror ch          \n      {ModifyRegister} selch opror1 setflags \n      {ModifyRegister} selch opror2 setflags'''
inst[0xd5] = f'''ror cl          \n      {ModifyRegister} selcl opror1 setflags \n      {ModifyRegister} selcl opror2 setflags'''




# 16-bit

inst[0xe1] = f'''addw b, b
    {RegisterToT} selbl
    {ModifyRegister} selbl opadd setflags
    {RegisterToT} selbh
    {ModifyRegister} selbh opadc setflags'''

inst[0xe2] = f'''addw b, c
    {RegisterToT} selcl
    {ModifyRegister} selbl opadd setflags
    {RegisterToT} selch
    {ModifyRegister} selbh opadc setflags'''

inst[0xe3] = f'''addw b, #LL
    {LoadLiteral} twr
    {ModifyRegister} selbl opadd setflags
    {LoadLiteral} twr
    {ModifyRegister} selbh opadc setflags'''
    
inst[0xe6] = f'''addw c, c
    {RegisterToT} selcl
    {ModifyRegister} selcl opadd setflags
    {RegisterToT} selch
    {ModifyRegister} selch opadc setflags'''



# Note:
# For the 16-bit inc/dec of b or c, the flags come from the low byte.
# setflags is asserted for the high byte, but the ALU operation (opci/opcd) only reads the user flags, and does not set them.

inst[0xf0] = f'''inc x          \n      {ModifyRegister} selx  opinc setflags'''
inst[0xf1] = f'''inc y          \n      {ModifyRegister} sely  opinc setflags'''
inst[0xf2] = f'''inc b          \n      {ModifyRegister} selbl opinc setflags   \n  {ModifyRegister} selbh opci setflags'''
inst[0xf3] = f'''inc c          \n      {ModifyRegister} selcl opinc setflags   \n  {ModifyRegister} selch opci setflags'''
inst[0xf4] = f'''dec x          \n      {ModifyRegister} selx  opdec setflags'''
inst[0xf5] = f'''dec y          \n      {ModifyRegister} sely  opdec setflags'''
inst[0xf6] = f'''dec b          \n      {ModifyRegister} selbl opdec setflags   \n  {ModifyRegister} selbh opcd setflags'''
inst[0xf7] = f'''dec c          \n      {ModifyRegister} selcl opdec setflags   \n  {ModifyRegister} selch opcd setflags'''

