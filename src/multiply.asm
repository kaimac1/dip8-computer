;mulitply (8bit x 8bit = 16bit result)
;b = x.y
    
        mov x, #254
        mov y, #199

        mov cl, x
        mov z, #1
loop    mov a, y        ; add if y & z
        and a, z
        jz noadd
        add bl, cl      ; b += c
        adc bh, ch
noadd   add cl, cl      ; c *= 2
        adc ch, ch
        add z, z        ; z *= 2
        jcc loop