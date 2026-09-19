/* The native tool-only branch already retains gift and umbrella priority.
   Resolve selected imported icon descriptors without indexing the short native
   table. Preserve full-width registers and HI/LO across the integer C query. */
.set noreorder
.set noat
.set gp=64
.section .text.af_v3_held_icon_hook,"ax",@progbits
.globl af_v3_held_icon_hook
.ent af_v3_held_icon_hook
af_v3_held_icon_hook:
    addiu $t7, $s0, -0x2224
    bltz $t7, native
    nop
    addiu $sp, $sp, -256
    sd $at, 16($sp)
    sd $v0, 24($sp)
    sd $v1, 32($sp)
    sd $a0, 40($sp)
    sd $a1, 48($sp)
    sd $a2, 56($sp)
    sd $a3, 64($sp)
    sd $t0, 72($sp)
    sd $t1, 80($sp)
    sd $t2, 88($sp)
    sd $t3, 96($sp)
    sd $t4, 104($sp)
    sd $t5, 112($sp)
    sd $t6, 120($sp)
    sd $t8, 136($sp)
    sd $t9, 144($sp)
    sd $ra, 152($sp)
    mfhi $t0
    sd $t0, 160($sp)
    mflo $t0
    sd $t0, 168($sp)
    sd $s0, 176($sp)
    sd $s1, 184($sp)
    sd $s2, 192($sp)
    sd $s3, 200($sp)
    sd $s4, 208($sp)
    sd $s5, 216($sp)
    sd $s6, 224($sp)
    sd $s7, 232($sp)
    sd $gp, 240($sp)
    sd $fp, 248($sp)
    jal af_v3_held_item_icon
    move $a0, $s0
    move $t7, $v0
    ld $t0, 160($sp)
    mthi $t0
    ld $t0, 168($sp)
    mtlo $t0
    ld $at, 16($sp)
    ld $v0, 24($sp)
    ld $v1, 32($sp)
    ld $a0, 40($sp)
    ld $a1, 48($sp)
    ld $a2, 56($sp)
    ld $a3, 64($sp)
    ld $t0, 72($sp)
    ld $t1, 80($sp)
    ld $t2, 88($sp)
    ld $t3, 96($sp)
    ld $t4, 104($sp)
    ld $t5, 112($sp)
    ld $t6, 120($sp)
    ld $t8, 136($sp)
    ld $t9, 144($sp)
    ld $s0, 176($sp)
    ld $s1, 184($sp)
    ld $s2, 192($sp)
    ld $s3, 200($sp)
    ld $s4, 208($sp)
    ld $s5, 216($sp)
    ld $s6, 224($sp)
    ld $s7, 232($sp)
    ld $gp, 240($sp)
    ld $fp, 248($sp)
    ld $ra, 152($sp)
    beqz $t7, unavailable
    addiu $sp, $sp, 256
    subu $t7, $t7, $t6
    b resume
    nop
native:
    lui $t7, 0x8011
    lw $t7, -0x2314($t7)
    addiu $t7, $t7, 0x22A8 /* Native tool descriptor base, 8085DD68. */
resume:
    addiu $sp, $sp, -16
    sd $ra, 8($sp)
    lui $ra, 0x8011
    lw $ra, -0x2314($ra)
    addiu $ra, $ra, 0x0E9C /* 8085C95C: a1 = t6 + t7. */
    addiu $sp, $sp, 16
    jr $ra
    ld $ra, -8($sp)
unavailable:
    /* Missing/disabled imported parents draw nothing, never an unrelated icon. */
    addiu $sp, $sp, -16
    sd $ra, 8($sp)
    lui $ra, 0x8011
    lw $ra, -0x2314($ra)
    addiu $ra, $ra, 0x1344 /* 8085CE04: native draw epilogue. */
    addiu $sp, $sp, 16
    jr $ra
    ld $ra, -8($sp)
.end af_v3_held_icon_hook
