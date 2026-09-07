.section .rodata
.balign 16
.globl af_npc_word_data
af_npc_word_data:
    .incbin "words.bin"
.globl af_npc_alias_data
af_npc_alias_data:
    .incbin "aliases.bin"
