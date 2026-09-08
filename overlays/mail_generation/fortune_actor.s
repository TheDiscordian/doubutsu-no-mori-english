.section .text.native,"ax",@progbits
.balign 16
.globl af_miko_native
af_miko_native:
    .incbin "native.bin"
    /* Preserve original BSS addresses without growing the loaded BSS. */
    .space 16

.section .rodata.fortune,"a",@progbits
.balign 16
.globl af_fortune_words
af_fortune_words:
    .incbin "words.bin"
