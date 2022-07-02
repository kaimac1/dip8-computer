
            mov b, #hello
            call printn

            mov b, #mystring
            call prints

            mov x, #$a5
            call printxh

            .byte $ff ; halt

hello       .byte "Hello, world!", $0a, 0
mystring    .string "The value of register x is: $"




UART = $f000

;print a null-terminated string
; b: string to print 

printn      mov c, #UART
pnloop      ldx b
            cmp x, #0
            jz pnret
            stx c
            inc b
            jmp pnloop
pnret       ret

            
;print a length-prefixed string (max len 255)
; b: string to print

prints      mov c, #UART
            ldx b           ; c = string length (8 bits)
psloop      inc b
            ldy b
            sty c
            dec x
            jnz psloop
            ret


;print an 8-bit hexadecimal value
; x: number to print

printxh     mov b, #hexdigits
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
            ret

hexdigits   .byte "0123456789abcdef"
