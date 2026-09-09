.set noreorder
.set noat
.text
.balign 4
.globl af_player_insect_name
af_player_insect_name:
    lhu     $a0, 0x021c($a2)
    jal     af_item_name_bridge
    move    $a1, $zero
    nop
    nop
    nop
    nop
.globl af_player_fish_name
af_player_fish_name:
    andi    $a0, $v0, 0xffff
    jal     af_item_name_bridge
    move    $a1, $zero
    nop
    nop
    nop
    nop
.globl af_player_dig_name
af_player_dig_name:
    lhu     $a0, 0x0d1c($t6)
    jal     af_item_name_bridge
    move    $a1, $zero
    nop
    nop
    nop
    nop
