.set noreorder
.section .text.entry,"ax"
.globl af_font_entry
af_font_entry:
    j af_accent_font_install
    nop
.section .rodata.resource,"a"
.balign 16
.globl af_font_resource
af_font_resource:
    .incbin "glyphs.bin"
