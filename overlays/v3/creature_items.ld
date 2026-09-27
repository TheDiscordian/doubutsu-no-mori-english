OUTPUT_ARCH(mips)
ENTRY(af_v3_creature_item_name)
af_creature_profile = 0x80465000;
SECTIONS {
    . = 0x804FF100;
    .text : { *(.text.af_v3_creature_item_name) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804FF900,"Creature readers overlap their metadata")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected creature reader state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
