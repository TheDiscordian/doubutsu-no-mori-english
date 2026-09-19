# Fixed-address counterpart of reader.c's museum case for the stable V2 ABI.
# The module descriptor ends at +0x88; this adapter owns +0x90..+0x100.
# Non-museum identities execute the two displaced instructions and resume.
.set noreorder
.section .text,"ax",@progbits
.globl af_museum_reader_name
af_museum_reader_name:
    lbu     $t0, 0x10($a1)
    addiu   $t1, $zero, 2
    beq     $t0, $t1, museum
    nop
    addiu   $sp, $sp, -32
    j       0x801984D8
    sw      $s2, 24($sp)
museum:
    addiu   $t0, $zero, 'M'
    sb      $t0, 0($a0)
    addiu   $t0, $zero, 'u'
    sb      $t0, 1($a0)
    addiu   $t0, $zero, 's'
    sb      $t0, 2($a0)
    addiu   $t0, $zero, 'e'
    sb      $t0, 3($a0)
    addiu   $t0, $zero, 'u'
    sb      $t0, 4($a0)
    addiu   $t0, $zero, 'm'
    sb      $t0, 5($a0)
    jr      $ra
    addiu   $v0, $zero, 6
