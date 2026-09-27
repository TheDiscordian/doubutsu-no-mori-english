.set noreorder
.set noat
.text
/* Both native constructors retain the player at caller sp+50. The original
 * message ID is in a0 after the unmodified call's argument delay slot. */
.globl af_v3_creature_fish_message_call
.type af_v3_creature_fish_message_call,@function
af_v3_creature_fish_message_call:
    move $a1,$a0
    j af_v3_creature_fish_message
    lw $a0,0x50($sp)
.size af_v3_creature_fish_message_call,.-af_v3_creature_fish_message_call
.globl af_v3_creature_insect_message_call
.type af_v3_creature_insect_message_call,@function
af_v3_creature_insect_message_call:
    move $a1,$a0
    j af_v3_creature_insect_message
    lw $a0,0x50($sp)
.size af_v3_creature_insect_message_call,.-af_v3_creature_insect_message_call
