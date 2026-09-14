OUTPUT_ARCH(mips)
ENTRY(af_v3_save_reset)
af_v3_save_check = 0x8046B400;
af_v3_save_pack = 0x8046B7A0;
af_v3_original_save_read = 0x8046BA60;
af_v3_original_save_clear = 0x8046BA70;
SECTIONS
{
    . = 0x80469200;
    .text : { *(.text.af_v3_save_reset) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046A200, "V3 save runtime overlaps field bridge")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected V3 save runtime state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
