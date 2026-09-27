OUTPUT_ARCH(mips)
ENTRY(af_v3_console_image_native_load)
af_console_pi_read = 0x80026500;
SECTIONS {
    . = 0x804F9020;
    .text : { *(.text.af_v3_console_image_native_load) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804FC820,"Console image code overlaps complete metadata")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected console loader globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
