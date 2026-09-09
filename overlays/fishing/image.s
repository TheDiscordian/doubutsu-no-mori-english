.set noreorder
.section .native,"ax",@progbits
.incbin "native.bin"
.space 16
.balign 16
.section .aliases,"a",@progbits
.balign 16
.global af_fishing_aliases
af_fishing_aliases:
.incbin "aliases.bin"
