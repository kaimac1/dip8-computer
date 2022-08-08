	.text
	.global	main

	;bare-metal setup
	mov b, #32768
	mov sp, b
	call main
	brk

main
	subsp #12
	mov   b, #4096
	stb   sp+1
	mov   b, #0
	stb   sp+3
	mov   b, #0
	stb   sp+5
	ldc   sp+5
l3
	ldb   sp+1
	addw  b, c
	stl #1, b
	addw  c, #1
	cmp   ch, #$1f
	jnz b0
	cmp   cl, #$ff
b0
	jcc   l3
	mov   c, #0
l17
	ldb   sp+1
	addw  b, c
	cmp   [b], #0
	jz    l12
	mov   b, c
	addw  b, c
	push  b		;spill
	addw  b, #3
	stb   sp+9
	pop   b		;unspill
	ldb   sp+7
	addw  b, c
	stb   sp+9
	stc   sp+5
	cmp   [sp+10], #$1f
	jnz b1
	cmp   [sp+9], #$ff
b1
	jcs   l21
	ldc   sp+9
l13
	ldb   sp+1
	addw  b, c
	stl #0, b
	addw  c, [sp+7]
	cmp   ch, #$1f
	jnz b2
	cmp   cl, #$ff
b2
	jcc   l13
l21
	ldc   sp+5
	ldb   sp+3
	addw  b, #1
	stb   sp+3
l12
	addw  c, #1
	cmp   ch, #$1f
	jnz b3
	cmp   cl, #$ff
b3
	jcc   l17
	ldc   sp+3
	addsp #12
	ret
; stacksize=0+??
