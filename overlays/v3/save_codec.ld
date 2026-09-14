OUTPUT_ARCH(mips)
ENTRY(af_v3_save_check)
SECTIONS
{
    . = 0x8046B400;
    .text : { *(.text.af_v3_save_check) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046BFF0, "V3 save codec exceeds the resident allocation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 save codec state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
