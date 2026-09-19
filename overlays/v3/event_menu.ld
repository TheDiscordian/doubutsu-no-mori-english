OUTPUT_ARCH(mips)
ENTRY(af_v3_event_menu_start)
SECTIONS
{
    . = 0x804AF000;
    .text : { *(.text.af_v3_event_menu_start) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804AFFF0, "Event menu exceeds module reservation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected event menu globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
