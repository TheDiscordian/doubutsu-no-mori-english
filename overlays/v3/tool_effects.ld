OUTPUT_ARCH(mips)
ENTRY(af_v3_shovel_call)
SECTIONS
{
    . = 0x804B2000;
    .text : { *(.text.af_v3_shovel_call) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B2FD0, "Tool effects overlap previous dig position")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected tool effects state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
