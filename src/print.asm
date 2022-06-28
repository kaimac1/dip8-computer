UART = $f000

;print a null-terminated string

            ldc #UART
            ldb #hello
loop        lda b
            cmp a, #0
            jz exit
            sta c
            inc bl
            jmp loop
exit        

            
;print a length-prefixed string

            ldb #mystring
            ldc b           ; c = string length (16 bits)
            inc bl
loop2       inc bl
            ldz b
            stz UART
            dec cl
            cmp cl, #0
            jnz loop2
            cmp ch, #0
            jnz loop2

            .byte $ff       ; halt


hello       .byte "Hello, world!", $0a, 0
mystring    .string "Lorem ipsum dolor sit amet"