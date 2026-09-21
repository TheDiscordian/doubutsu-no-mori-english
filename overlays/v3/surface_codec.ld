OUTPUT_ARCH(mips)
ENTRY(af_v3_save_check_extended)
af_v3_reward_data_valid = 0x8046B408;
af_v3_surface_profile_byte = 0x804BC900;
SECTIONS {
    . = 0x804BD000;
    .text : { *(.text.af_v3_save_check_extended) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804BE000,"Surface codec exceeds its checked page")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected surface codec state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
