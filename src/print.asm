
            ldb #hello
            call printn

            ldb #mystring
            call prints

            mov a, #$3f
            call printah

            .byte $ff ; halt

hello       .byte "Hello, world!", $0a, 0
mystring    .string "The value of register a is: $"




UART = $f000

;print a null-terminated string
; b: string to print 

printn      ldc #UART
pnloop      lda b
            cmp a, #0
            jz pnexit
            sta c
            inc bl
            jmp pnloop
pnexit      ret

            
;print a length-prefixed string
; b: string to print

prints      ldc b           ; c = string length (16 bits)
            inc bl
psloop      inc bl
            ldz b
            stz UART
            dec cl
            cmp cl, #0
            jnz psloop
            cmp ch, #0
            jnz psloop
            ret


;print an 8-bit hexadecimal value
; a: number to print

printah     ldb #hexdigits
            mov cl, #0
ahloop      cmp a, #16      ; while a >= 16
            jcc ahout       
            sub a, #16
            inc cl
            jmp ahloop
ahout       mov t, cl       ; cl = hi nib
            ldz b+t
            stz UART
            mov t, a        ; a = low nib
            ldz b+t
            stz UART
            ret

hexdigits   .byte "0123456789abcdef"
