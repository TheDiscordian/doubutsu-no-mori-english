/* Hook only aHNW_set_talk_info_dance's final mDemo_Set_msg_num call.
 * Its incoming sp+20 contains the original Haniwa_c pointer; +18 is message.
 * Keep the native table lookup in the original call's delay slot.
 */
.set noreorder
.set noat
.set mips3
.section .text.af_gyroid_default_demo, "ax"
.globl af_gyroid_default_demo
.ent af_gyroid_default_demo
af_gyroid_default_demo:
    lw      $a1, 0x20($sp)
    addiu   $sp, $sp, -24
    sw      $ra, 20($sp)
    jal     af_gyroid_default_select
    addiu   $a1, $a1, 0x18
    lw      $ra, 20($sp)
    move    $a0, $v0
    j       0x8007B5C0
    addiu   $sp, $sp, 24
.end af_gyroid_default_demo
