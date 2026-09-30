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
#ifdef AF_HP_HARVEST_REGISTRY
    ori $at, $zero, 0xd0d2
#elif defined(AF_HP_REWARD_REGISTRY)
    ori $at, $zero, 0xd0d1
#elif defined(AF_HP_CARRIED_REGISTRY)
    ori $at, $zero, 0xd0ce
#elif defined(AF_HP_FESTIVAL_REGISTRY)
    ori $at, $zero, 0xd0cd
#elif defined(AF_HP_EXERCISE_REGISTRY)
    ori $at, $zero, 0xd0b4
#else
    ori $at, $zero, 0xd0ae
#endif
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

/* Native NPC-manager area-15 allocation. The checked call replaces the store
 * at 80A23C5C; its delay slot keeps v1=255 for successful initialization.
 * s0 is the event-info pointer and v0 is the allocation result. On failure,
 * reset the native uninitialized sentinel and return through the original
 * false-result epilogue, 0x5c bytes after this call's return address. */
.globl af_hp_manager_alloc
af_hp_manager_alloc:
    bne $v0, $zero, 2f
     sw $v0, 0($s0)
    addiu $t0, $zero, 70
    sw $t0, 4($s0)
    addiu $t0, $zero, -1
    sw $t0, 8($s0)
    addu $v1, $zero, $zero
    addiu $ra, $ra, 0x5c
2:  jr $ra
     nop
