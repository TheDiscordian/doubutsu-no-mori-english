.set noreorder
.set noat
.text
.globl af_credits_line
af_credits_line:
    blez    $a2, done
     addu   $t0, $a1, $a2
    addiu   $t2, $zero, 0x20
trim:
    lbu     $t1, -1($t0)
    addiu   $t0, $t0, -1
    bne     $t1, $t2, draw
     nop
    addiu   $a2, $a2, -1
    bgtz    $a2, trim
     nop
done:
    jr      $ra
     nop
draw:
    j       0x80090E1C
     nop
