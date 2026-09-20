OUTPUT_ARCH(mips)
ENTRY(af_v3_event_stock_construct)
SECTIONS
{
    . = 0x804AE000;
    .text : { *(.text.af_v3_event_stock_construct) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804AE690, "Event stock code overlaps shared deferred rewards")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected event stock globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
