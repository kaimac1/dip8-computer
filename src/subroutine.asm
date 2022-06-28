; subroutine calls

main    mov a, #1
        call subr       ; call subroutine
        mov a, #3
        jmp next

subr    mov a, #2
        ret             ; pop return address & jump



next    .byte $ff




        push x
        push y
        push reta
        jmp subr

subr    pop b [reta]
        pop y
        pop x
        push b
        ...
        ..
        ..
        ret




inlined parameters:

        push reta
        jump subr
        .db 01, 02, 03
        ..resume..

subr    pop b   [reta]
        mov ch, bh
        mov cl, bl      ; c=b
        add bl, #3
        adc bh, #0
        push b
        ...do stuff with parameters using c...

        lda c+#0        macro: mov t,#0; lda c+t
        ..
        lda c+#1
        ..
        etc.

        ret



non-local parameter block:

        push <params
        push >params
        call subr

subr    pop b       ;ret addr
        pop c       ;params addr
        push b
        ..
        ..
        ret


params  .db 01, 02, 03


