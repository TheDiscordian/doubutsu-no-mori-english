# Dedicated title overlay ownership outside the unchanged four-MiB game heap.
# Called instead of Actor_get_overlay_area at its native call site.
.set noreorder
.set noat
.section .text,"ax",@progbits
.globl af_title_allocate
af_title_allocate:
    lui $t0, 0x8010
    ori $t0, $t0, 0x21f0
    bne $a0, $t0, ordinary
    nop
    lui $t0, 0x8000
    lw $t0, 0x0318($t0)
    lui $t1, 0x0080
    bne $t0, $t1, unavailable
    lui $t0, 0x8040
    addiu $t0, $t0, 16
    lui $t1, 0xaf54
    ori $t1, $t1, 0xc0de
    addu $t2, $t0, $a2
    sw $t1, -16($t0)
    sw $t1, -12($t0)
    sw $t1, -8($t0)
    sw $t1, -4($t0)
    sw $t1, 0($t2)
    sw $t1, 4($t2)
    sw $t1, 8($t2)
    sw $t1, 12($t2)
    jr $ra
    sw $t0, 16($a0)
unavailable:
    jr $ra
    sw $zero, 16($a0)
ordinary:
    j 0x800578e0
    nop
