size  = 8191
flags = $4000

        mov  b, $feff
        mov  sp, b

        ; set all flags to true
        mov  b, #flags
        mov  c, #size
loop1   stl  #1, b
        inc  b
        dec  c
        jnz  loop1
        cmp  ch, #0
        jnz  loop1

        ;main loop
        mov  c, #0
loop2   ldx  c + #flags     ; if flags[c] == 1
        cmp  x, #0
        jz   next
        mov  b, c           ; prime = i + i + 3
        addw b, c 
        addw b, #3      
        stb  prime
        addw b, c           ; k = prime + i
        stc  isave
_inloop cmp  bh, #>size     ; while k < size
        jnz  cmpout
        cmp  bl, #<size
_cmpout jcs  cntup
        stl  #0, b + #flags   ; flags[k] = 0
        addw b, [prime]       ; k += prime
        jmp  inloop
_cntup  ldc  isave
        addw [count], #1    ; count++
_next   inc  c              ; i++
        cmp  ch, #>size
        jnz  cmpo2
        cmp  cl, #<size
_cmpo2  jcc  loop2

        ldb  count
        brk

isave .word 0
count .word 0 
prime .word 0
