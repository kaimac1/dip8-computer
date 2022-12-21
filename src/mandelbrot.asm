UART = $ff00
UART_DR = $ff03

X0_LEFT = $-0200
Y0_TOP  = $-0100
MAXCOUNT = 14
XCOLS = 96
YROWS = 35
XSTEP = 8  ; 256 * 3.0/XCOLS
YSTEP = 15 ; 256 * 2.0/YROWS

; Variables in RAM
.varstart $4000
py      = .var byte
px      = .var byte
x0      = .var word ;X0_LEFT
y0      = .var word ;Y0_TOP
xval    = .var word
yval    = .var word
ival    = .var word
xsq     = .var word
ysq     = .var word
x2py2   = .var word
square_table = .var array 256 word



                sig
                mov b, $feff        ; set up stack ptr
                mov sp, b

                mov b, #UART        ; init 88C92 uart
                adr b+2
                stl $20             ; reset
                stl $30
                stl $40
                stl $b0
                adr b
                stl $00             ; normal baud rate table
                stl $13             ; 8 bits no parity
                stl $07             ; 1 stop bit
                stl $cc, b+1        ; 38400 baud
                stl $05, b+2        ; enable TX/RX

                call square8_init

                mov b, #0           ; zero init
                stbl px
                stbl py
                stb ival
                mov b, #X0_LEFT     ; init
                stb x0
                mov b, #Y0_TOP
                stb y0


top             call mandelbrot
                ldx ival            ; print char[ival]
                mov b, #chars
                ldy b+x
                sty UART_DR

                addw [x0], #XSTEP   ; x0 += XSTEP
                add [px], #1        ; px += 1
                cmp [px], #XCOLS
                jcc top

                stl $0a, UART_DR    ; newline
                stl #0, px          ; px = 0
                mov b, #X0_LEFT     ; x0 = X0_LEFT
                stb x0
                addw [y0], #YSTEP   ; y0 += YSTEP
                add [py], #1        ; py += 1
                cmp [py], #YROWS
                jcc top
                
                brk

chars   .byte " ..,,~~=+:xOX# "


mandelbrot      mov b, #0
                stb xval
                stb yval
                stbl ival

_loop           ldb xval
                call square         ; x*x
                stb xsq
                ldb yval
                call square         ; y*y
                stb ysq
                ldc xsq
                addw c, b           ; c = x^2 + y^2
                stc x2py2

                cmp ch, #$04
                jnz skipcmp
                cmp cl, #$00
_skipcmp        jcs done            ; done if c > 4

                subw c, b           ; c = x^2
                subw c, b           ; c = x^2 - y^2
                addw c, [x0]
                ldb xval            ; x = xold
                stc xval            ; xnew = x^2 - y^2 + x0
                addw b, [yval]      ; b = x+y
                call square         ; b = (x+y)^2
                subw b, [x2py2]     ; b = (x+y)^2 - x^2 - y^2   = 2*x*y
                addw b, [y0]
                stb yval            ; y = 2*x*y + y0

                add [ival], #1
                cmp m, #MAXCOUNT
                jcs done
                jmp loop
_done           ret




sqtemp = .var word


; Square the signed 16-bit value in b
; output in c
square          cmp bh, #0          ; make input positive
                jns domul
                mov c, #0
                subw c, b
                mov b, c
_domul          mov y, bh
                mov x, bl           ; al in x, ah in y
                mov ch, #0

                mov bh, #0          ; al.al = al^2
                addw b, b
                ldb b + #square_table
                mov cl, bh

                mov bl, y           ; ah.ah = ah^2
                mov bh, #0
                addw b, b
                ldb b + #square_table
                add ch, bl                


                stc sqtemp          
                ; Could use mulb to multiply two 8-bit values here
                ; but it's slightly faster to use the square table:
                ;   xy = [(x+y)^2 - x^2 - y^2]/2
                ; mov bl, x
                ; mov bh, y
                ; call mulb
                ; mov c, b

                mov bl, y
                add bl, x               ; al.ah
                mov bh, #0
                addw b,b
                ldc b + square_table        ; c = (x+y)^2
                mov bl, x
                mov bh, #0
                addw b,b
                subw c, [b+square_table]    ; c -= x^2
                mov bl, y
                mov bh, #0
                addw b,b
                subw c, [b+square_table]    ; c -= y^2
                sig ; clr carry
                ror ch
                ror cl

                ldb sqtemp
                addw b, c
                addw b, c           ; ah.al
                ret









;multiply (8x8 bit = 16 bit result)
; bh, bl   inputs
; b        16-bit output
; preserves y, c

mulb            mov x, #0
                sig             ; clear carry
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


