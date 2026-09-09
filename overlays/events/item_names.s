.set noreorder
.set noat
.text
.balign 4

.macro item_call name, size, slot=0
.globl \name
\name:
.endm
.macro finish_call size, slot=0
    jal     af_item_name_bridge
    addiu   $a1, $zero, \slot
    .space  \size - 12, 0
.endm

item_call af_room_first_name, 36
    move    $a0, $a1
    finish_call 36
item_call af_room_second_name, 36
    move    $a0, $a1
    finish_call 36
item_call af_police_name, 36
    lhu     $a0, 0x6294($a1)
    finish_call 36
item_call af_angler_name, 28
    lhu     $a0, 0x0944($s0)
    finish_call 28
item_call af_redd_outside_name, 36, 2
    move    $a0, $a1
    finish_call 36, 2
item_call af_saharah_name, 28
    lhu     $a0, 0x003a($sp)
    finish_call 28
item_call af_opening_nook_name, 36
    move    $a0, $a1
    finish_call 36
