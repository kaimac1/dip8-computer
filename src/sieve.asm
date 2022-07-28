size  = $1fff
flags = $4000

        mov b, $8000
        mov sp, b

        ; set all flags to true
        mov b, #flags
        mov c, #size
loop1   stl #1, b
        inc b
        dec c
        jnz loop1
        cmp ch, #0
        jnz loop1

        ;main loop
        mov c, #0
loop2   ldx c + #flags  ; if flags[c] == 1
        cmp x, #0
        jz next
        mov b, c        ; prime = c + c + 3
        addw b, c 
        addw b, #3      
        stb prime
        addw b, c       ; k = prime + c
clflags cmp bh, #>size  ; while k < size
        jnz cmpout
        cmp bl, #<size
cmpout  jcs countup
        stl #0, b + #flags ; flags[k] = 0
        stc isave        ; k += prime
        ldc prime
        addw b, c
        ldc isave
        jmp clflags
countup ldb count       ; count++
        inc b
        stb count
next    inc c
        cmp ch, #>size
        jnz cmpo2
        cmp cl, #<size
cmpo2   jcc loop2

        ldb count
        brk

isave .word 0
count .word 0 
prime .word 0
