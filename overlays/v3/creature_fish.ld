OUTPUT_ARCH(mips)
ENTRY(af_v3_fish_position)
af_fish_sin = 0x80099A94;
af_fish_cos = 0x80099A54;
af_fish_values = 0x80649400;
SECTIONS {
    . = 0x80647400;
    .text : { *(.text.af_v3_fish_position) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80648000,"Fish world code overlaps field tables")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected fish globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
