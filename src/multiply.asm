
        ;8x8=16 multiply
        ;x.y=b
    
        lda #254
        mov x, a
        mov cl, a
        lda #199
        mov y, a
        lda #1
        mov z, a

loop    mov a,y     ; add if y & z
        mov t,z
        and a,t
        jz noadd
        mov t,cl    ; b += c
        add bl,t
        mov t,ch
        adc bh,t
noadd   mov t,cl    ; c *= 2
        add cl,t
        mov t,ch
        adc ch,t
        mov t,z     ; z *= 2
        add z,t
        jcc loop