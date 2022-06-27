UART = $f000

;print a null-terminated string

            ldc #UART
            ldb #hello

loop        lda b
            ldt #0
            cmp a,t
            jz exit
            sta c
            inc bl
            jmp loop
exit        

            
;print a length-prefixed string

            ldb #mystring
            ldc b
            inc bl
loop2       inc bl
            ldz b
            stz UART
            dec cl
            ldt #0
            cmp cl, t
            jnz loop2
            ldt #0
            cmp ch, t
            jnz loop2

            .byte $ff       ; halt


hello       .byte "Hello, world!", $0a, 0
mystring    .string "Lorem ipsum dolor sit amet"