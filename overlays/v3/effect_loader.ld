OUTPUT_ARCH(mips)
ENTRY(af_v3_effect_profile_load)
af_effect_native_load = 0x800263C0;
af_effect_dma = 0x80026B44;
af_effect_crc = 0x80195938;
af_effect_fault = 0x80029AB4;
SECTIONS {
    . = 0x80A1C6A0;
    .text : { *(.text.af_v3_effect_profile_load) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80A1CAA0, "Effect loader exceeds checked scene extension")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected effect-loader state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
