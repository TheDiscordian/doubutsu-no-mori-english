OUTPUT_ARCH(mips)
ENTRY(af_v3_surface_profile_byte)
af_v3_require_save_state = 0x804692F4;
af_v3_save_halt = 0x80469270;
af_v3_save_collect = 0x8046B9C4;
af_surface_prior_record = 0x80466E58;
af_surface_prior_owned = 0x80466E98;
af_surface_prior_clear = 0x8046B59C;
SECTIONS {
    . = 0x804BC900;
    .text : { *(.text.af_v3_surface_profile_byte) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804BCFF0,"Surface save helpers overlap packet guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected surface helper state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
