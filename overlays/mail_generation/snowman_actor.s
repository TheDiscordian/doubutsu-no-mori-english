.set noreorder
.set noat
.section .text.native,"ax"
.incbin "native.bin"

.section .rodata.snapshots,"a"
.balign 16
.globl af_snowman_templates
af_snowman_templates:
.incbin "snapshots.bin"
