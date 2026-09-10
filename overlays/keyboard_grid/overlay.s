.section .native,"ax",@progbits
.incbin "previous.bin"
.section .rodata.grid,"a",@progbits
.balign 16
.global af_grid_tables
af_grid_tables:
.incbin "keys.bin"
.balign 16
.global af_grid_keycap
af_grid_keycap:
.incbin "keycap.bin"
