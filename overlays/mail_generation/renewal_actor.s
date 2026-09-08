.section .text.native,"ax",@progbits
.balign 16
.globl af_renewal_native
af_renewal_native:
    .incbin "native.bin"
.section .text.creator,"ax",@progbits
.balign 4
    .incbin "creator.bin"
