.set noreorder
.set noat
.text
/* Each native fish owns its relocated river/coastal program at actor+244.
 * These helpers target complete retained coastal functions, not patched entry
 * prologues or guessed heap addresses. Installation must verify their owners.
 */
.macro native name, address
.globl \name
.type \name,@function
\name:
    lw $t9,0x244($a0)
    addiu $t9,$t9,(\address-0x80A98F60)
    jr $t9
    nop
.size \name,.-\name
.endm
native af_patrol_player_near,0x80A99B84
native af_patrol_search,0x80A999D0
native af_patrol_setup,0x80A9ACA8
native af_patrol_old_swim,0x80A99F58
native af_patrol_old_wait,0x80A99E6C
native af_patrol_old_escape,0x80A9A910
native af_patrol_old_swim_init,0x80A9A9A4
native af_patrol_old_wait_init,0x80A9AC0C
native af_patrol_old_escape_init,0x80A9AC88
