OUTPUT_ARCH(mips)
ENTRY(af_v3_save_check_extended)
af_v3_reward_data_valid = 0x8046B408;
SECTIONS
{
    . = 0x8046D000;
    .text : { *(.text.af_v3_save_check_extended) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046D8DC, "Reward codec overlaps retained item-reader entries")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected reward codec state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
