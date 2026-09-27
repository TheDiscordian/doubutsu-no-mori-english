OUTPUT_ARCH(mips)
ENTRY(af_v3_console_room_move)
SECTIONS {
    . = 0x804FB000;
    .text : { *(.text.af_v3_console_room_move) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804FC000,"Console room code overlaps bindings")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected console room globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
