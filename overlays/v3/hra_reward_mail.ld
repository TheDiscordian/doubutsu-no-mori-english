OUTPUT_ARCH(mips)
SECTIONS
{
    . = AF_HRA_MAIL_RAM;
    .text : { *(.text .text.*) . = ALIGN(16); }
    .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(SIZEOF(.data) == 0, "HRA reward mail contains writable data")
    ASSERT(SIZEOF(.bss) == 0, "HRA reward mail retains mutable state")
    ASSERT(. <= 0x80B10000, "HRA reward mail exceeds the original creator allocation")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
