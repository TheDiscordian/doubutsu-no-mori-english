.set noreorder
.set noat
.section .text.af_v3_shovel_call, "ax"
.globl af_v3_shovel_call
.ent af_v3_shovel_call
af_v3_shovel_call:
    /* mPlib_Check_scoop_after's checked 680-byte frame stores its actual
       PLAYER_ACTOR at sp+676. Preserve the four native status arguments;
       the extra o32 word carries the source golden flag. */
    addiu   $sp, $sp, -32
    sw      $ra, 28($sp)
    lw      $t0, 708($sp)
    lb      $t0, 0x1117($t0)
    xori    $t0, $t0, 90
    sltiu   $t0, $t0, 1
    jal     af_v3_shovel_status
    sw      $t0, 16($sp)
    lw      $ra, 28($sp)
    jr      $ra
    addiu   $sp, $sp, 32
.end af_v3_shovel_call
