OUTPUT_ARCH(mips)
ENTRY(af_v3_furniture_reward_goods)
af_v3_furniture_import_profile = 0x80465000;
af_v3_native_reward_goods = 0x800BFCF0;
af_v3_reward_random = 0x8002C9AC;
SECTIONS {
    . = 0x80474BC0;
    .text : { *(.text.af_v3_furniture_reward_goods) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80474FE0, "Reward code exceeds its guarded accessory gap")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected reward state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
