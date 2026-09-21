OUTPUT_ARCH(mips)
ENTRY(af_v3_surface_catalogue_bit)
af_v3_catalogue_owned = 0x80469AD4;
SECTIONS {
    . = 0x804BF000;
    .text : { *(.text.af_v3_surface_catalogue_bit) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804BF400,"Surface menu helper overlaps category tables")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected surface menu state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
