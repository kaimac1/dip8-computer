; multiply two 8-bit values together and print the 16-bit result


            ; set up stack pointer
            mov b, #$1000
            mov sp, b

            ldx var1
            call printxh
            mov b, #string1
            call prints
            ldx var2
            call printxh
            mov b, #string2
            call prints

            ldx var1
            ldy var2
            call mulxy      ; multiply

            mov x, bh
            call printxh
            mov x, bl
            call printxh

            .byte $ff
string1     .string " multiplied by "
string2     .string " is "

var1        .byte 123
var2        .byte 234





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

;print an 8-bit hexadecimal value
; x   number to print
; y   clobbered
; bc  saved

printxh     push b
            mov b, #hexdigits
            mov y, #0
xhloop      cmp x, #16      ; while x >= 16
            jcc xhout
            sub x, #16
            inc y
            jmp xhloop
xhout       ldy b+y         ; y = hi nib
            sty UART
            ldy b+x         ; x = low nib
            sty UART
            pop b
            ret

hexdigits   .byte "0123456789abcdef"



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
