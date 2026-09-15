/* Existing whole-unit callers retain live values in caller-saved registers.
 * Preserve them when replacing their previously analysed private callees.
 * The C helpers return through v0 and do not use HI/LO or floating-point state.
 */
.set noreorder
.set noat
.set gp=64
.text
.macro bridge name, target
.globl \name
.ent \name
\name:
    addiu $sp, $sp, -144
    sd $v1, 16($sp)
    sd $a0, 24($sp)
    sd $a1, 32($sp)
    sd $a2, 40($sp)
    sd $a3, 48($sp)
    sd $t0, 56($sp)
    sd $t1, 64($sp)
    sd $t2, 72($sp)
    sd $t3, 80($sp)
    sd $t4, 88($sp)
    sd $t5, 96($sp)
    sd $t6, 104($sp)
    sd $t7, 112($sp)
    sd $t8, 120($sp)
    sd $t9, 128($sp)
    sd $ra, 136($sp)
    jal \target
    nop
    ld $v1, 16($sp)
    ld $a0, 24($sp)
    ld $a1, 32($sp)
    ld $a2, 40($sp)
    ld $a3, 48($sp)
    ld $t0, 56($sp)
    ld $t1, 64($sp)
    ld $t2, 72($sp)
    ld $t3, 80($sp)
    ld $t4, 88($sp)
    ld $t5, 96($sp)
    ld $t6, 104($sp)
    ld $t7, 112($sp)
    ld $t8, 120($sp)
    ld $t9, 128($sp)
    ld $ra, 136($sp)
    jr $ra
    addiu $sp, $sp, 144
.end \name
.endm
#ifdef AF_V3_TOWN_ELIGIBLE_BRIDGE
bridge af_v3_town_eligible_bridge, af_v3_town_eligible
#elif defined(AF_V3_DISPLAY_ROSTER_BRIDGE)
bridge af_v3_all_display_clothing_index_bridge, af_v3_all_display_clothing_index
#else
bridge af_v3_roster_clothing_source_bridge, af_v3_roster_clothing_source
bridge af_v3_roster_clothing_index_bridge, af_v3_roster_clothing_index
bridge af_v3_roster_outfit_ready_bridge, af_v3_roster_outfit_ready
bridge af_v3_roster_clothing_record_bridge, af_v3_roster_clothing_record
#endif
