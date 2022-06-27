;print a null-terminated string

            ldc #$f000      ; uart
            ldb #hello

loop        lda b
            ldt #0
            cmp a,t
            jz exit
            sta c
            inc bl
            jmp loop
exit        
            .byte $ff       ; halt

hello   .byte "Hello, world!", 0

