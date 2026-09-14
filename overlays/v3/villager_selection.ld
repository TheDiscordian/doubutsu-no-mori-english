OUTPUT_ARCH(mips)
ENTRY(af_v3_unseen_personality)
SECTIONS
{
    . = 0x80463400;
    .text : { *(.text.af_v3_unseen_personality) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80464000, "V3 selection code overlaps the shared villager reader")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "V3 selection state needs explicit ownership")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
