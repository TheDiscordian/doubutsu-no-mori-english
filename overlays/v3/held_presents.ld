OUTPUT_ARCH(mips)
ENTRY(af_v3_present_pocket)
SECTIONS
{
    . = 0x804B4000;
    .text : { *(.text.af_v3_present_pocket) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B4F00, "Wrapped-item helpers overlap their source table")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected wrapped-item state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
