UART = $ff00
RAM = $8000

            sig
            mov b, $feff
            mov sp, b

start       ldx RAM
            call printxh
            stl $0a, UART   ; newline

            ldx RAM         ; inc val
            add x, #1
            stx RAM

            jmp start




; start       mov b, #hello
; printn      mov c, #UART
; _loop       ldx b
;             cmp x, #0
;             jz return
;             stx c
;             inc b
;             jmp loop
; _return     jmp start

; hello       .byte "Hello, world!", $0a, 0

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