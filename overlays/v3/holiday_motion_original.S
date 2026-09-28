.set noreorder
.set noat
.section .text.af_holiday_animation_original,"ax",@progbits
.globl af_holiday_animation_original
.ent af_holiday_animation_original
af_holiday_animation_original:
    # Replay the checked original prologue, then enter the live owner at +8.
    # a0-a3, ra, and every incoming stack argument remain intact.
    lui $t9,0x8013
    lw $t9,0x6eec($t9)
    lw $t9,0x104($t9)
    addiu $t9,$t9,8
    addiu $sp,$sp,-80
    jr $t9
    sw $s0,44($sp)
.end af_holiday_animation_original
