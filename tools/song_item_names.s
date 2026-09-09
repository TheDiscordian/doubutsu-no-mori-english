.set noreorder
.set noat
.text
.globl af_song_set_item
af_song_set_item:
    andi $t0, $a1, 0xFF
    or $a1, $a0, $zero
    j 0x800BB6A0
    addiu $a0, $t0, 0x2A00
