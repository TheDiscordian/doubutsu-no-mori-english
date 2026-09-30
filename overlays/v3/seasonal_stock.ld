OUTPUT_ARCH(mips)
ENTRY(af_v3_seasonal_stock)
SECTIONS {
    . = 0x804F3500;
    .text : { *(.text.af_v3_seasonal_stock) *(.text .text.*) }
    ASSERT(. <= 0x804F37E0,"Seasonal stock code overlaps its records")
    .rodata 0x804F37E0 : {
        *(.rodata .rodata.*)
        ASSERT(. <= 0x804F37F0,"Seasonal stock code overlaps its choice word");
        . = 0x10;
        *(.seasonal_choice)
    }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804F3800,"Seasonal stock overlaps its guard")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected seasonal stock state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
