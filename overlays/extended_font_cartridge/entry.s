.set noreorder
.section .text,"ax",@progbits
.globl af_font_entry
af_font_entry:
    j af_font_install
    nop

.section .rodata,"a",@progbits
.balign 16
.globl af_font_resource
af_font_resource:
    .incbin "glyphs.bin"
