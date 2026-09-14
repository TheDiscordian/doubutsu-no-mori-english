OUTPUT_ARCH(mips)
ENTRY(af_v3_mail_source_name)
SECTIONS
{
    . = 0x80465400;
    .text : { *(.text.af_v3_mail_source_name) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80465800, "V3 villager readers exceed their reservation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "V3 villager readers have unexpected state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
