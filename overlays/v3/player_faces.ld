OUTPUT_ARCH(mips)
ENTRY(af_v3_player_eye_sequence)
SECTIONS
{
    . = 0x804B4540;
    .text : { *(.text.af_v3_player_eye_sequence) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B4700, "Player face readers overlap their bounded table")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected face-reader state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
