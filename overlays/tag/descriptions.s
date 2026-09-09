.set noreorder
.section .description_hook,"ax",@progbits
.globl af_tag_description_hook
af_tag_description_hook:
  move $a0, $s0
  lw $a1, 0x44($sp)
  jal af_tag_description_prepare
  lw $a2, 0x3c($sp)
  move $a2, $v0
  move $a0, $s0
  li $a1, 1
  j af_tag_description_resume
  nop

.section .quest_names,"ax",@progbits
.globl af_tag_quest_names
af_tag_quest_names:
  .incbin "quest.bin"

.section .native_head,"ax",@progbits
  .incbin "native.bin", 0, 0x87fc
.section .native_tail,"ax",@progbits
  .incbin "native.bin", 0x8bb4
