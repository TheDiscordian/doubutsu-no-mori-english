.set noreorder
.set noat
.section .native,"ax",@progbits
.incbin "previous.bin"
.text
# The generated trampoline includes only inspected original instructions and
# a relocatable jump back after the overwritten entry. No PC-relative words.
.include "trampolines.s"
