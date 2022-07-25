; multiply two 8-bit values together and print the 16-bit result in decimal

            ; set up stack pointer
            mov b, #$8000
            mov sp, b

            ;ldx var1
            ;call printdx
            ;mov b, #string1
            ;call prints
            ;ldx var2
            ;call printdx
            ;mov b, #string2
            ;call prints

            ldbh var1
            ldbl var2
            call mulb

            ;call printdb

            brk
string1     .string " x "
string2     .string " = "

var1        .byte 70
var2        .byte 69




;multiply (8x8 bit = 16 bit result)
; bh, bl   inputs
; b        16-bit output

mulb        mov x, #0
            mov y, #8
            add x, #0       ; clear carry
            ror bl          ; lsr bl
            jcc mbn1
            add x, bh
mbn1        ror x
            ror bl
            jcc mbn2
            add x, bh
mbn2        ror x
            ror bl
            jcc mbn3
            add x, bh
mbn3        ror x
            ror bl
            jcc mbn4
            add x, bh
mbn4        ror x
            ror bl
            jcc mbn5
            add x, bh
mbn5        ror x
            ror bl
            jcc mbn6
            add x, bh
mbn6        ror x
            ror bl
            jcc mbn7
            add x, bh
mbn7        ror x
            ror bl
            jcc mbn8
            add x, bh
mbn8        ror x
            ror bl
            mov bh, x
            ret





UART = $f000


; used by printdx and print db
; prints a single digit
;  b    16-bit input number / remainder output
;  c    multiple of ten (1, 10, 100, 1000, ...) to print
;  x    1 if any previous digits have been printed (so leading zeros are not printed)

dodigit     mov y, #0
calcloop    cmp bh, ch          ; compare b and c
            jnz calc2
            cmp bl, cl
calc2       jcc calcout
            sub bl, cl          ; b = b - c
            sbc bh, ch
            inc y
            jmp calcloop
calcout     cmp y, #0           ; now y = b div c
            jnz skipcheck
            cmp x, #0
            jz  calcret
skipcheck   mov x, #1
calcwrite   add y, '0'          ; create ascii code
            sty UART
calcret     ret

;print an 8-bit value as decimal
; x   number to print

printdx     mov bh, #0
            mov bl, x
            mov x, #0
            jmp print8bit

;print an 16-bit value as decimal
; b   number to print

printdb     mov x, #0
            mov c, #10000
            call dodigit
            mov c, #1000
            call dodigit
print8bit   mov c, #100
            call dodigit
            mov c, #10
            call dodigit
            mov c, #1
            call dodigit
            ret





;print a length-prefixed string (max len 255)
; b   string to print
; xyc clobbered

prints      mov c, #UART
            ldx b           ; c = string length (8 bits)
psloop      inc b
            ldy b
            sty c
            dec x
            jnz psloop
            ret
