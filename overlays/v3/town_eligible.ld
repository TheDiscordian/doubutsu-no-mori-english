OUTPUT_ARCH(mips)
ENTRY(af_v3_town_eligible)
SECTIONS
{
    . = 0x80473E40;
    .text : { *(.text.af_v3_town_eligible) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80474000, "Town eligibility overlaps accessory registry")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected town helper state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
