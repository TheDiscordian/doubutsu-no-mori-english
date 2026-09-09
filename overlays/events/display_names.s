# Independent assembly for the guarded festival calls and reserve-name sequence.
.set noreorder
.set noat
.section .text.call,"ax",@progbits
    jal 0x80195D20
.section .text.length,"ax",@progbits
    addiu $a3, $zero, 8
.section .text.reserve_name,"ax",@progbits
    addiu $a0, $sp, 0x24
    ori $a2, $zero, 0xd008
    jal 0x80196044
    addiu $a1, $zero, 8
    beq $v0, $zero, reserve_resume
    lui $a0, 0x8014
    addiu $a0, $a0, 0x2410
    addiu $a1, $zero, 1
    addiu $a2, $sp, 0x24
    jal 0x8009D6D0
    addiu $a3, $zero, 8
