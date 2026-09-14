OUTPUT_ARCH(mips)
ENTRY(af_v3_asset_init)
SECTIONS
{
    . = 0x80460100;
    .text : { *(.text.af_v3_asset_init) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80461000, "V3 asset code overlaps object table")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "V3 asset helper has unexpected state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
