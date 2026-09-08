.set noreorder
.section .text.af_glyph_load_texture,"ax",@progbits
.globl af_glyph_load_texture
af_glyph_load_texture:
    # Preserve the native loader prologue and its complete six-argument frame.
    addiu $sp, $sp, -32
    sw $ra, 20($sp)
    sw $a0, 32($sp)
    sw $a1, 36($sp)
    sw $a2, 40($sp)
    sw $a3, 44($sp)
    jal af_glyph_texture_code
    move $a0, $a1
    sw $v0, 36($sp)
    j 0x800906B4
    nop
