OUTPUT_ARCH(mips)
SECTIONS
{
    . = 0x80925E48;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(SIZEOF(.rodata) == 0, "HRA rewards add unexpected data")
    ASSERT(SIZEOF(.data) == 0, "HRA rewards contain writable data")
    ASSERT(SIZEOF(.bss) == 0, "HRA rewards retain mutable state")
    ASSERT(. <= 0x809260A4, "HRA rewards exceed the checked score-letter wrapper")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
