.section .rodata
.balign 16
.global af_secret_templates
af_secret_templates:
.incbin "snapshots.bin"
.section .note.GNU-stack,"",@progbits
