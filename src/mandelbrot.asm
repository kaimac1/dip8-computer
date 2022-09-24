UART = $f000

X0_LEFT = $-0200
Y0_TOP  = $-0100
MAXCOUNT = 14
XCOLS = 96
YROWS = 35
XSTEP = 8  ; 256 * 3.0/XCOLS
YSTEP = 15 ; 256 * 2.0/YROWS


                mov b, $8000
                mov sp, b
                call square8_init

top             call mandelbrot

                ldx ival            ; print char[ival]
                mov b, #chars
                ldy b+x
                sty UART

                addw [x0], #XSTEP   ; x0 += XSTEP
                add [px], #1        ; px += 1
                cmp [px], #XCOLS
                jcc top

                stl $0a, UART       ; newline
                stl #0, px          ; px = 0
                mov b, #X0_LEFT     ; x0 = X0_LEFT
                stb x0

                addw [y0], #YSTEP   ; y0 += YSTEP
                add [py], #1        ; py += 1
                cmp [py], #YROWS
                jcc top

                ret

chars   .byte " ..,,~~=+:xOX# "
py      .byte 0
px      .byte 0
x0      .word X0_LEFT
y0      .word Y0_TOP
xval    .word 0
yval    .word 0
ival    .byte 0
xsq     .word 0
ysq     .word 0
x2py2   .word 0

mandelbrot      mov b, #0
                stb xval
                stb yval
                stbl ival

_loop           ldb yval
                call square         ; y*y
                stc ysq
                ldb xval
                call square         ; x*x
                stc xsq                
                ldb ysq
                addw c, b           ; c = x^2 + y^2
                stc x2py2

                cmp ch, #$04
                jnz skipcmp
                cmp cl, #$00
_skipcmp        jcs done            ; done if c > 4

                subw c, b           ; c = x^2
                subw c, b           ; b = x^2 - y^2
                addw c, [x0]
                ldb xval            ; x = xold
                stc xval            ; xnew = x^2 - y^2 + x0
                addw b, [yval]      ; b = x+y
                call square         ; c = (x+y)^2
                subw c, [x2py2]     ; c = (x+y)^2 - x^2 - y2   = 2*x*y
                addw c, [y0]
                stc yval            ; y = 2*x*y + y0

                ldx ival
                inc x
                cmp x, #MAXCOUNT
                stx
                jcs done
                jmp loop
_done           ret



; only one input, b
; output in c
square          cmp bh, #0  ; make input positive
                jns domul
                mov c, #0
                subw c, b
                mov b, c
_domul          mov y, bh
                mov x, bl       ; al in x, ah in y

                mov ch, #0

                ;call square8    ; al.al
                mov bh, #0
                addw b, b
                ldb b + #square_table
                mov cl, bh

                mov bl, y       ; ah.ah
                ;call square8
                mov bh, #0
                addw b, b
                ldb b + #square_table
                add ch, bl                
                
                mov bh, x       ; al.ah
                call mulb
                addw c, b
                addw c, b       ; ah.al
                ret






;multiply (8x8 bit = 16 bit result)
; bh, bl   inputs
; b        16-bit output
; preserves y, c

mulb            mov x, #0
                add x, #0       ; clear carry
                mov t, bh
                ror bl          ; lsr bl
                jcc bit1
                add x, t
_bit1           ror x
                ror bl
                jcc bit2
                add x, t
_bit2           ror x
                ror bl
                jcc bit3
                add x, t
_bit3           ror x
                ror bl
                jcc bit4
                add x, t
_bit4           ror x
                ror bl
                jcc bit5
                add x, t
_bit5           ror x
                ror bl
                jcc bit6
                add x, t
_bit6           ror x
                ror bl
                jcc bit7
                add x, t
_bit7           ror x
                ror bl
                jcc bit8
                add x, t
_bit8           ror x
                ror bl
                mov bh, x
                ret


; initialise lookup table
square8_init    mov y, #0
_loop           mov bl, y
                mov bh, y
                call mulb
                mov ch, #0
                mov cl, y
                addw c, c ; c = 2*y
                stb c + #square_table
                inc y
                cmp y, #0
                jnz loop
                ret

; input:  bl
; output: b
square8         mov bh, #0
                addw b, b
                ldb b + #square_table
                ret

square_table .byte 0
    ; 512 byte table here


