# Runs from the original watchdog's vacated body at 0x800D64F0.
# The module is loaded before the heap or its clients can overwrite this region.
.set noreorder
.set noat
.section .bootstrap,"ax",@progbits
.balign 4
    addiu $sp, $sp, -40
    sw $ra, 36($sp)
    sw $s0, 32($sp)
    sw $s1, 28($sp)
    or $s0, $a0, $zero
    or $s1, $a1, $zero
    lui $t0, 0x8019
    addiu $t0, $t0, 0x48e0
    bne $a0, $t0, failed
    lui $t0, 0x0026
    ori $t0, $t0, 0xb720
    bne $s1, $t0, failed
    lui $a1, 0x0280
    jal 0x80026b44 # DmaMgr_RequestSync
    addiu $a2, $zero, 0x4000
    bne $v0, $zero, failed
    lui $t0, 0x4146
    ori $t0, $t0, 0x5254
    lw $t1, 0($s0)
    bne $t0, $t1, failed
    addiu $t0, $zero, 1
    lw $t1, 4($s0)
    bne $t0, $t1, failed
    addiu $t0, $zero, 0x4000
    lw $t1, 8($s0)
    bne $t0, $t1, failed
    or $a0, $s0, $zero
    jal 0x8002fe00 # osWritebackDCache
    addiu $a1, $zero, 0x4000
    or $a0, $s0, $zero
    jal 0x80034ce0 # osInvalICache
    addiu $a1, $zero, 0x4000
    or $a0, $s0, $zero
    jal 0x80194be0 # af_runtime_init
    or $a1, $s1, $zero
    addiu $a0, $s0, 0x4000
    addiu $a1, $s1, -0x4000
    lui $t0, 0x8014
    sw $a1, 0x589c($t0) # gSystemHeapSize
    jal 0x8002bf78 # SystemHeap_Init
    nop
    lw $ra, 36($sp)
    lw $s0, 32($sp)
    lw $s1, 28($sp)
    jr $ra
    addiu $sp, $sp, 40
failed:
    b failed
    nop
