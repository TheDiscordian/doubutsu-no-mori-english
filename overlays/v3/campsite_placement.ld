OUTPUT_ARCH(mips)
ENTRY(af_v3_tent_set_class)
SECTIONS {
    . = 0x804A2A70;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A2B00, "Tent classification overlaps event index")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "No implicit placement state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
