;mulitply (8bit x 8bit = 16bit result)
;b = cl.y



            mov cl, #254
            mov y,  #199

    mulbit  .byte 1

2   mulxy   mov ch, #0
5           st  mulbit, #1   ; ldm mulbit ; stm #1
1   mloop   mov x, y        ; add if y & bit
4           and x, mulbit   ; ldm mulbit ; andxm
3           jz  mnoadd
1           add bl, cl      ; b += c
1           adc bh, ch
1   mnoadd  add cl, cl      ; c *= 2
1           adc ch, ch
4           ld  x, mulbit   ; mulbit <<= 1
2           add mulbit, x   ; mov t,x ; addmt
3           jcc mloop
1           ret
>> 29




store mulbit at sp+0:

            mov cl, #254
            mov y,  #199

2   mulxy   mov ch, #0
3           st  #1, sp      ; ldm sp ; stm #1
1   mloop   mov x, y        ; add if y & bit
2           and x, [sp]     ; ldm sp ; andxm
3           jz  mnoadd
1           add bl, cl      ; b += c
1           adc bh, ch
1   mnoadd  add cl, cl      ; c *= 2
1           adc ch, ch
2           ld  x, sp       ; ldm sp ; ldx m
2           add [sp], x     ; mov t,x ; addmt
3           jcc mloop
1           ret
>> 23


; add sp, #32     ; sp = sp + 32
; add [sp], #32    ; mem[sp] = mem[sp] + 32

