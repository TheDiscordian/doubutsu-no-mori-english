/* Tail hooks own the constructor epilogue, not a new actor allocation. */
.set noreorder
.set noat
.text
.align 2
.globl af_v3_npc_voice_tail
.ent af_v3_npc_voice_tail
af_v3_npc_voice_tail:
    jal af_v3_npc_voice
    addiu $a0, $sp, 0x58
    sw $v0, 0x930($s0)
    lw $ra, 0x24($sp)
    lw $s0, 0x20($sp)
    jr $ra
    addiu $sp, $sp, 0xC0
.end af_v3_npc_voice_tail
.globl af_v3_npc2_voice_tail
.ent af_v3_npc2_voice_tail
af_v3_npc2_voice_tail:
    jal af_v3_npc_voice
    addiu $a0, $sp, 0x50
    sw $v0, 0x930($s0)
    lw $ra, 0x24($sp)
    lw $s0, 0x20($sp)
    jr $ra
    addiu $sp, $sp, 0xB8
.end af_v3_npc2_voice_tail
