# Test-only raw Controller Pak reader. Runs in privately allocated fixture RAM.
# a0 points to exactly 32 KiB of writable output. Returns the native I/O error.
# No write, format, repair, or deletion function is called.
.set noreorder
.set noat
.text
.balign 16
.globl af_test_read_pak
af_test_read_pak:
    addiu $sp, $sp, -48
    sw $ra, 44($sp)
    sw $s0, 40($sp)
    sw $s1, 36($sp)
    sw $s2, 32($sp)
    sw $s3, 28($sp)
    move $s0, $a0
    move $s1, $zero
    jal 0x800D6A10
    move $s3, $zero
    move $s2, $v0
1:
    move $a0, $s2
    move $a1, $zero
    move $a2, $s1
    jal 0x800391B0
    move $a3, $s0
    bnez $v0, 2f
    move $s3, $v0
    addiu $s1, $s1, 1
    addiu $s0, $s0, 32
    sltiu $t0, $s1, 1024
    bnez $t0, 1b
    nop
2:
    jal 0x800D6A44
    move $a0, $s2
    move $v0, $s3
    lw $s3, 28($sp)
    lw $s2, 32($sp)
    lw $s1, 36($sp)
    lw $s0, 40($sp)
    lw $ra, 44($sp)
    jr $ra
    addiu $sp, $sp, 48
