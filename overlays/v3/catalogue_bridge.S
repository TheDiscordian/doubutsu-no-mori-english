.set noreorder
.set noat
.set gp=64
.text
.globl af_v3_original_catalogue_program
af_v3_original_catalogue_program:
    addiu $sp, $sp, -48
    sw $s0, 32($sp)
    j af_v3_catalogue_program_continue
    nop

#ifdef AF_V3_CLOTHING_CATALOGUE
.globl af_v3_original_catalogue_furniture_init
af_v3_original_catalogue_furniture_init:
    addiu $sp, $sp, -72
    sw $s0, 32($sp)
    j af_v3_catalogue_furniture_continue
    nop
#endif

.globl af_v3_catalogue_type
af_v3_catalogue_type:
    addiu $sp, $sp, -32
    sd $ra, 24($sp)
    sw $s1, 0($sp)
    addiu $ra, $zero, 2
    sw $ra, 4($sp)
    jal af_v3_room_query
    nop
    lw $v1, 8($sp)
    ld $ra, 24($sp)
    addiu $sp, $sp, 32
    j af_v3_catalogue_type_continue
    nop
