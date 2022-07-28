            ; init sp
            mov b, #$8000
            mov sp, b
    

            mov b, #hello
            call printn

            mov b, #mystring
            call prints

            mov x, #$a5
            call printxh

            brk
hello       .byte "Hello, world!", $0a, 0
mystring    .string "The value of register x is: $"




UART = $f000

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
