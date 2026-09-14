OUTPUT_ARCH(mips)
ENTRY(af_v3_startup)
af_crc32 = 0x80195938;
SECTIONS
{
    . = 0x8019A8E0;
    .text : { *(.text.af_v3_startup) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8019ACC0, "V3 startup overlaps configuration")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "V3 startup has unexpected state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
