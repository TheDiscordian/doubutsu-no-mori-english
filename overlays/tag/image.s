.set noreorder
.section .native,"ax",@progbits
.incbin "native.bin"
.space 288
.balign 16
.section .labels,"a",@progbits
.globl af_tag_labels
af_tag_labels:
.incbin "labels.bin"
