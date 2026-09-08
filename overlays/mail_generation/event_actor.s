.section .text.native,"ax",@progbits
.balign 16
.globl af_event_native
af_event_native:
    .incbin "native.bin"
    .space 304
.section .text.creator,"ax",@progbits
.balign 4
    .incbin "creator.bin"
