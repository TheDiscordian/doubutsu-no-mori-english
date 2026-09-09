.section .native,"ax",@progbits
.incbin "native.bin"
/* Retain the original notice object's BSS address, including all editor state. */
.space 128,0
