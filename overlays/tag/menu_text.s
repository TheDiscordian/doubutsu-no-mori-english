.set noreorder
.set noat
.section .text,"ax",@progbits
.globl af_tag_throw_fit
af_tag_throw_fit:
    lw $t0, 0($a0)
    slti $at, $t0, af_tag_throw_cells
    beqz $at, 1f
    nop
    addiu $t0, $zero, af_tag_throw_cells
    sw $t0, 0($a0)
1:
    j af_tag_width_resume
    nop
