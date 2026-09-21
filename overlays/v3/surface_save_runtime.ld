OUTPUT_ARCH(mips)
ENTRY(af_v3_save_reset)
af_v3_save_check = 0x8046B400;
af_v3_save_pack = 0x8046B7A0;
af_v3_original_save_read = 0x8046BA60;
af_v3_original_save_clear = 0x8046BA70;
af_v3_surface_profile_byte = 0x804BC900;
SECTIONS {
    . = 0x804BE000;
    .text : { *(.text.af_v3_save_reset) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804BFFF0,"Surface save runtime overlaps complete packet guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected surface save runtime state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
