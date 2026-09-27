.set noreorder
.set noat
.text
.globl af_v3_creature_release_index
.type af_v3_creature_release_index,@function
af_v3_creature_release_index:
    /* Constructor continuation: preserve its live arguments and native slots.
       t6 is the carried item, s0 the release actor, and t7 the result. */
    addiu $t7,$t6,-0x2300
    sltiu $at,$t7,32
    bnez $at,1f
    nop
    addiu $t7,$t7,4
1:
    sw $t7,0x178($s0)
    jr $ra
    nop
.size af_v3_creature_release_index,.-af_v3_creature_release_index
