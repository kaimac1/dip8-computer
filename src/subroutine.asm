; subroutine calls

main    mov a, #1
        call subr       ; call subroutine
        mov a, #3
        jmp stack

subr    mov a, #2
        ret             ; pop return address & jump



; pass parameters via stack

stack   mov x, #4
        mov y, #5
        push x
        push y
        call subr2
        jmp inline

subr2   pop b           ; pop retaddr
        pop y
        pop x
        push b          ; re-push retaddr
        mov a, x
        mov a, y
        ret 



; in-line parameters

inline  call add3
        .byte $02, $03, $04     ; params placed after call
        jmp pblock              ; call returns to here
        

add3    pop b
        mov ch, bh
        mov cl, bl
        add bl, #3      ; correct return address - add 3
        adc bh, #0
        push b
        ; now access parameters using c
        lda c
        mov t, #1
        ldz c+t
        add a, z
        mov t, #2
        ldz c+t
        add a, z
        ret



; subroutine parameter block
; (non-reentrant)

; when the assmebler can handle expressions,
; another way to load arguments would be:
;  mov a, #2
;  sta add4params
;  mov a, #3
;  sta add4params + 1
;  etc.

pblock  ldb #add4params
        mov a, #2
        sta b
        inc bl
        mov a, #3
        sta b
        inc bl
        mov a, #4
        sta b
        inc bl
        mov a, #5
        sta b
        
        call add4
        .byte $ff


add4params .byte 0, 0, 0, 0     ; parameters stored before subroutine
add4    ldb #add4params
        lda b
        inc bl
        ldz b
        add a,z
        inc bl
        ldz b
        add a,z
        inc bl
        ldz b
        add a,z
        ret