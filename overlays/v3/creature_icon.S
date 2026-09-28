/* Default item-descriptor branch. Gift and native tool branches stay intact. */
.set noreorder
.set noat
.set gp=64
.text
#ifdef AF_DIARY_ICON
#define ICON_HOOK af_diary_icon_hook
#define ICON_QUERY af_diary_item_icon
#else
#define ICON_HOOK af_v3_creature_icon_hook
#define ICON_QUERY af_v3_creature_icon
#endif
.globl ICON_HOOK
.type ICON_HOOK,@function
ICON_HOOK:
#ifdef AF_DIARY_ICON
    addiu $t9,$s0,-0x2B10
    sltiu $t9,$t9,16
    beqz $t9,native
    nop
#else
    addiu $t9,$v1,-3
    beqz $t9,creature
    addiu $t9,$v1,-13
    bnez $t9,native
    nop
creature:
    sltiu $t9,$v0,32
    bnez $t9,native
    nop
#endif
    addiu $sp,$sp,-256
    sd $at,16($sp)
    sd $v0,24($sp)
    sd $v1,32($sp)
    sd $a0,40($sp)
    sd $a1,48($sp)
    sd $a2,56($sp)
    sd $a3,64($sp)
    sd $t0,72($sp)
    sd $t1,80($sp)
    sd $t2,88($sp)
    sd $t3,96($sp)
    sd $t4,104($sp)
    sd $t5,112($sp)
    sd $t6,120($sp)
    sd $t7,128($sp)
    sd $t8,136($sp)
    sd $ra,152($sp)
    mfhi $t0
    sd $t0,160($sp)
    mflo $t0
    sd $t0,168($sp)
    sd $s0,176($sp)
    sd $s1,184($sp)
    sd $s2,192($sp)
    sd $s3,200($sp)
    sd $s4,208($sp)
    sd $s5,216($sp)
    sd $s6,224($sp)
    sd $s7,232($sp)
    sd $gp,240($sp)
    sd $fp,248($sp)
    jal ICON_QUERY
    move $a0,$s0
    move $t9,$v0
    ld $t0,160($sp)
    mthi $t0
    ld $t0,168($sp)
    mtlo $t0
    ld $at,16($sp)
    ld $v0,24($sp)
    ld $v1,32($sp)
    ld $a0,40($sp)
    ld $a1,48($sp)
    ld $a2,56($sp)
    ld $a3,64($sp)
    ld $t0,72($sp)
    ld $t1,80($sp)
    ld $t2,88($sp)
    ld $t3,96($sp)
    ld $t4,104($sp)
    ld $t5,112($sp)
    ld $t6,120($sp)
    ld $t7,128($sp)
    ld $t8,136($sp)
    ld $ra,152($sp)
    ld $s0,176($sp)
    ld $s1,184($sp)
    ld $s2,192($sp)
    ld $s3,200($sp)
    ld $s4,208($sp)
    ld $s5,216($sp)
    ld $s6,224($sp)
    ld $s7,232($sp)
    ld $gp,240($sp)
    ld $fp,248($sp)
    beqz $t9,unavailable
    addiu $sp,$sp,256
    move $a1,$t9
    lw $a0,0xCC($sp)
    lui $t9,0x8011
    lw $t9,-0x2314($t9)
    addiu $t9,$t9,0xEC0 /* Resume at 8085C980 with native category/palette logic. */
    jr $t9
    nop
native:
#ifdef AF_DIARY_ICON
    j af_diary_prior_icon
    nop
#else
    lui $t9,0x8011
    lw $t9,-0x2314($t9)
    addiu $t9,$t9,0x29A0 /* Actual relocated item_tex_data_table, 8085E460. */
    addu $t9,$t9,$t8
    lw $t9,0($t9)
    sll $t1,$v0,3
    lw $a0,0xCC($sp)
    addu $a1,$t9,$t1
    lui $t9,0x8011
    lw $t9,-0x2314($t9)
    addiu $t9,$t9,0xEC0
    jr $t9
    nop
#endif
unavailable:
    lui $t9,0x8011
    lw $t9,-0x2314($t9)
    addiu $t9,$t9,0x1344 /* Native draw epilogue; never index past a table. */
    jr $t9
    nop
.size ICON_HOOK,.-ICON_HOOK
