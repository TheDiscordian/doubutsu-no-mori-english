OUTPUT_ARCH(mips)
ENTRY(af_v3_pocket_index)
af_v3_room_value = 0x80468000;
af_v3_original_pocket_index = 0x8046B100;
af_v3_original_pocket_count = 0x8046B110;
SECTIONS
{
    . = 0x8046B200;
    .text : { *(.text.af_v3_pocket_index) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046BFF0, "V3 pocket searches exceed the resident allocation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 pocket state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
