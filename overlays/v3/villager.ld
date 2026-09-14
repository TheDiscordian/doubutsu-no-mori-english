OUTPUT_ARCH(mips)
ENTRY(af_v3_load_name)
SECTIONS
{
    . = 0x80464000;
    .text : { *(.text.af_v3_load_name) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80467FF0, "V3 villager code exceeds owned reservation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "V3 villager helper has unexpected state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
