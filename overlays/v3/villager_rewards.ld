OUTPUT_ARCH(mips)
ENTRY(af_v3_house_reward)
SECTIONS
{
    . = 0x80463A00;
    .text : { *(.text.af_v3_house_reward) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80464000, "V3 house rewards overlap the villager reader")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "V3 rewards must not add mutable globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
