OUTPUT_ARCH(mips)
ENTRY(af_v3_save_check_extended)
SECTIONS
{
    . = 0x8046D000;
    .text : { *(.text.af_v3_save_check_extended) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046DBF0, "V3 clothing codec exceeds its ROM and RAM reservation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 clothing codec state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
