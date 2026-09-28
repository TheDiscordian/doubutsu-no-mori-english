/* Both native NPC controllers already construct a relocated row pointer in
 * t1, pass the final special name in v1, and expect a profile at sp+56.
 * Extend that shared camper hook; never index a native table with an added ID.
 * Only at/t1 are scratch registers, matching the existing helper contract. */
.set noreorder
.set noat
.set nomacro
.text
.globl af_hp_spawn_profile
af_hp_spawn_profile:
    ori $at, $zero, 0xd0a0
    sltu $at, $v1, $at
    bne $at, $zero, 1f
     nop
    ori $at, $zero, 0xd0ae
    sltu $at, $v1, $at
    beq $at, $zero, 1f
     nop
    andi $at, $v1, 0xff
    addiu $at, $at, -0xa0
    sll $at, $at, 1
    lui $t1, %hi(af_hp_spawn_profiles)
    addu $t1, $t1, $at
    lh $t1, %lo(af_hp_spawn_profiles)($t1)
    jr $ra
     sh $t1, 0x56($sp)
1:  j af_hp_previous_spawn_profile
     nop
