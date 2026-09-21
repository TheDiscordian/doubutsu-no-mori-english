.set noreorder
.set noat
.section .stock_bridge,"ax",@progbits
.globl af_surface_prior_stock_list
af_surface_prior_stock_list:
    addiu $sp,$sp,-32
    sw $ra,20($sp)
    j 0x800BF8F0
    nop
