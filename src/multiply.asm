; multiply two 8-bit values together and print the 16-bit result in decimal

            ; set up stack pointer
            mov b, #$1000
            mov sp, b


            ldx var1
            call printdx
            mov b, #string1
            call prints
            ldx var2
            call printdx
            mov b, #string2
            call prints

            ldx var1
            ldy var2
            call mulxy      ; multiply

            call printdb

            .byte $ff
string1     .string " x "
string2     .string " = "

var1        .byte 70
var2        .byte 69





;mulitply (8bit x 8bit = 16bit result)
; xy  inputs
; b   output
; c   clobbered

mulbit      .byte 1

mulxy       mov b, #0
            mov cl, x
            mov ch, #0
            stl #1, mulbit
mloop       mov x, y        ; add if y & bit
            and x, [mulbit]
            jz  mnoadd
            add bl, cl      ; b += c
            adc bh, ch
mnoadd      add cl, cl      ; c *= 2
            adc ch, ch
            adr mulbit      ; bit *= 2
            ldx
            add x, x
            stx
            jcc mloop
            ret





UART = $f000

nonzero     .byte 0

dodigit     mov y, #0
calcloop    cmp bh, ch
            jnz calc2
            cmp bl, cl
calc2       jcc calcout
            sub bl, cl
            sbc bh, ch
            inc y
            jmp calcloop
calcout     cmp y, #0
            jz  checknz         ; if y == 0: checknz
            stl #1, nonzero     ; if y != 0: nonzero=1
            jmp calcwrite
checknz     mov c, #0
            cmp cl, [nonzero]
            jz  calcret
calcwrite   add y, '0'          ; create ascii code
            sty UART
calcret     ret

;print an 8-bit value as decimal
; x   number to print

printdx     stl #0, nonzero
            mov b, #0
            add bl, x
            jmp print8bit

;print an 16-bit value as decimal
; b   number to print

printdb     stl #0, nonzero
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
