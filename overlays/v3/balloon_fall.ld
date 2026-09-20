OUTPUT_ARCH(mips)
ENTRY(af_v3_balloon_getup)
af_v3_balloon_fly = 0x804AC778;
af_v3_balloon_request = 0x804B1100;
af_v3_tool_getup = 0x804A5E18;
SECTIONS
{
    . = 0x804ACBE0;
    .text : { *(.text.af_v3_balloon_getup) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804ACFF0, "Balloon fall overlaps category guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected balloon fall state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
