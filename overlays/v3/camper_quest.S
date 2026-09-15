/* GC uses the winter camper profile for D08F too. Preserve the relocated
 * native table pointer for every other identity, and the caller's frame. */
.set noreorder
.set noat
.set nomacro
.text
.globl af_v3_camper_profile
af_v3_camper_profile:
    ori $at, $zero, 0xd08f
    beq $v1, $at, 1f
     nop
    lh $t1, 0($t1)
    jr $ra
     sh $t1, 0x56($sp)
1:  addiu $t1, $zero, 0x23
    jr $ra
     sh $t1, 0x56($sp)

/* a0 = full actor ID, a1 = native first-meeting flag. The winter and summer
 * normal-init functions have identical lifecycle logic in the donor. Share
 * native modes 4/5; separate summer English message selection is still needed.
 * GC sets the summer-session flag at talk start, not at greeting completion. */
.globl af_v3_camper_talk_mode
af_v3_camper_talk_mode:
    ori $t0, $zero, 0xd08f
    beq $a0, $t0, 2f
     addiu $v0, $zero, 1
    ori $t0, $zero, 0xd05e
    bne $a0, $t0, 4f
     nop
    beq $zero, $zero, 3f
     nop
2:  addiu $t0, $zero, 1
    bne $a1, $t0, 4f
     addiu $v0, $zero, 5
    lui $t1, %hi(camper_greeted)
    sb $t0, %lo(camper_greeted)($t1)
3:  addiu $t0, $zero, 1
    bne $a1, $t0, 4f
     addiu $v0, $zero, 5
    addiu $v0, $zero, 4
4:  jr $ra
     nop
