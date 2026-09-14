OUTPUT_ARCH(mips)
ENTRY(af_v3_feng_range)
af_v3_room_query = 0x804680B8;
SECTIONS
{
    . = 0x80931780;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80932960, "V3 feng shui owner exceeds its 8-KiB image bound")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected feng shui suffix state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
