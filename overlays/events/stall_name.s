.set noreorder
.set noat
.text
.balign 4
.globl af_stall_full_name
af_stall_full_name:
    sll     $t8, $s1, 4
    sll     $t9, $s1, 2
    addu    $t0, $s6, $t9
    addu    $a0, $s5, $t8
    sw      $a0, 0($t0)
    lhu     $a2, 0($s2)
    jal     af_load_item_name
    addiu   $a1, $zero, 16
