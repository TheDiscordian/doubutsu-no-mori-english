OUTPUT_ARCH(mips)
ENTRY(af_v3_melody_start)
SECTIONS
{
    . = 0x80473500;
    .text : { *(.text.af_v3_melody_start) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80474000, "Expanded melody helper overlaps accessory registry")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Expanded melody helper has unexpected state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
