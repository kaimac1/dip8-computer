;mulitply (8bit x 8bit = 16bit result)
;b = x.y
    
        mov x, #254
        mov y, #199

        mov cl, x
        mov z, #1
loop    mov a, y        ; add if y & z
        mov t, z
        and a, t
        jz noadd
        mov t, cl       ; b += c
        add bl, t
        mov t, ch
        adc bh, t
noadd   mov t, cl       ; c *= 2
        add cl, t
        mov t, ch
        adc ch, t
        mov t, z        ; z *= 2
        add z, t
        jcc loop