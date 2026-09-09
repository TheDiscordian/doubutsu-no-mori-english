.set noreorder
.section .native,"ax",@progbits
.incbin "native.bin"
/* Retain every original BSS address, initializing through the file DMA. */
.space 352,0
.section .secret_table,"a",@progbits
.balign 16
.global af_secret_templates
af_secret_templates:
.incbin "snapshots.bin"
