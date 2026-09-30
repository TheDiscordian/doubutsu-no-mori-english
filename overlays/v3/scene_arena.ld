OUTPUT_ARCH(mips)
ENTRY(af_v3_scene_init)
SECTIONS {
    . = 0x804F3280;
    .text : { *(.text.af_v3_scene_init) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804F4900,"Scene allocator overlaps borrowed-owner state")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected scene allocator state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
