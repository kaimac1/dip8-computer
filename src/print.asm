            ; init sp
            mov b, #$8000
            mov sp, b
    

            ;mov b, #hello
            ;call printn

            ;mov b, #mystring
            ;call prints

            mov b, #59999
            call printdb

            brk
hello       .byte "Hello, world!", $0a, 0
mystring    .string "The value of register x is "




UART = $ff03

;print a null-terminated string
; b: string to print 

printn      mov c, #UART
_loop       ldx b
            cmp x, #0
            jz return
            stx c
            inc b
            jmp loop
_return     ret


;print a length-prefixed string (max len 255)
; b: string to print

prints      mov c, #UART
            ldx b           ; c = string length (8 bits)
_loop       inc b
            ldy b
            sty c
            dec x
            jnz loop
            ret


;print an 8-bit hexadecimal value
; x   number to print
; y   clobbered
; bc  saved

printxh     push b
            mov b, #hexdigits
            mov y, #0
_loop       cmp x, #16      ; while x >= 16
            jcc write
            sub x, #16
            inc y
            jmp loop
_write      ldy b+y         ; y = hi nib
            sty UART
            ldy b+x         ; x = low nib
            sty UART
            pop b
            ret

hexdigits   .byte "0123456789abcdef"



; used by printdx and print db
; prints a single digit
;  b    16-bit input number / remainder output
;  c    multiple of ten (1, 10, 100, 1000, ...) to print
;  x    1 if any previous digits have been printed (so leading zeros are not printed)
dodigit     mov y, #0
_loop       cmp bh, ch          ; compare b and c
            jnz skipcmp
            cmp bl, cl
_skipcmp    jcc calcout
            sub bl, cl          ; b = b - c
            sbc bh, ch
            inc y
            jmp loop
_calcout    cmp y, #0           ; now y = b div c
            jnz cprint   
            cmp x, #0
            jz  cret
_cprint     mov x, #1
            add y, '0'          ; create ascii code
            sty UART
_cret       ret


;print an 8-bit value as decimal
; x   number to print
printdx     mov bh, #0
            mov bl, x
            mov x, #0
            jmp print8bit


;print an 16-bit value as decimal
; b   number to print
printdb     mov x, #0
            mov c, #10000
            call dodigit
            mov c, #1000
            call dodigit
print8bit   mov c, #100
            call dodigit
            mov c, #10
            call dodigit
            mov c, #1
            call dodigit
            ret

