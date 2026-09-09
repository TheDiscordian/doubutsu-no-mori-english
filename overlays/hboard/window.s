.set noreorder
.set noat
.text
.globl af_hboard_window_bridge
af_hboard_window_bridge:
    lw      $t0,0x2c($a0)
    lui     $t1,1
    addu    $t0,$t0,$t1
    lw      $t0,0x6e0($t0)
    beq     $t0,$zero,1f
    nop
    lw      $t9,0x30($t0)
    beq     $t9,$zero,1f
    nop
    jr      $t9
    nop
1:  jr      $ra
    nop
