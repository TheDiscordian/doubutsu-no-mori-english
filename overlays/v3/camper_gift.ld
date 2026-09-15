OUTPUT_ARCH(mips)
ENTRY(af_v3_camper_gift)
camper_last_gift = 0x804A1A12;
native_clear = 0x8002F4C0;
SECTIONS {
    . = 0x804A2F30;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A2FF0, "Camper gift tracker overlaps package guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "No implicit gift state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
