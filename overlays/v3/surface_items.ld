OUTPUT_ARCH(mips)
ENTRY(af_v3_surface_item_name)
af_surface_prior_name = 0x80467300;
af_surface_prior_type = 0x804AA000;
af_surface_prior_price = 0x80467574;
SECTIONS {
    . = 0x804BC000;
    .text : { *(.text.af_v3_surface_item_name) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804BC800,"Surface item code overlaps complete metadata")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected surface item state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
