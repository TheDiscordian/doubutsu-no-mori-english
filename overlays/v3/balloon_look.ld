OUTPUT_ARCH(mips)
ENTRY(af_v3_balloon_look)
SECTIONS
{
    . = 0x804AEAA0;
    .text : { *(.text.af_v3_balloon_look) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804AEF00, "Balloon look overlaps event stock")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected balloon look state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
