.set noreorder
.set noat
.section .text.af_v3_tool_rod_lifetime, "ax"
.globl af_v3_tool_rod_lifetime
.ent af_v3_tool_rod_lifetime
af_v3_tool_rod_lifetime:
    /* Native LoadOrDestruct still loads the real model first. Only its final
       rod/bobber lifetime comparison uses a family, from the requested t4.
       Recreate the replaced li at,34; every other live register is retained. */
    addiu   $at, $t4, -87
    sltiu   $at, $at, 2
    beqz    $at, 1f
    nop
    addiu   $t4, $zero, 34
1:
    jr      $ra
    addiu   $at, $zero, 34
.end af_v3_tool_rod_lifetime
