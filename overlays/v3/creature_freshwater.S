.set noreorder
.set noat
.text
/* Complete retained services in the actor's relocated freshwater program. */
.macro native name, address
.globl \name
.type \name,@function
\name:
    lw $t9,0x244($a0)
    addiu $t9,$t9,(\address-0x809317D0)
    jr $t9
    nop
.size \name,.-\name
.endm
native af_fresh_player_near,0x8093246C
native af_fresh_search,0x80932298
native af_fresh_wall,0x809325CC
native af_fresh_flow_reverse,0x80932188
native af_fresh_flow,0x809321B8
native af_fresh_setup,0x8093382C
