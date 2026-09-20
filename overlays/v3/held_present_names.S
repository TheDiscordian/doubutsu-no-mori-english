.set noreorder
.section .text.af_v3_present_original_name,"ax",@progbits
.globl af_v3_present_original_name
af_v3_present_original_name:
    addiu $sp,$sp,-64
    j 0x80096748
    sw $ra,20($sp)
