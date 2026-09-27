OUTPUT_ARCH(mips)
ENTRY(af_v3_insect_slot)
SECTIONS {
    . = AF_INSECT_RAM;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    . = ALIGN(16);
    af_insect_bss_start = .;
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    . = ALIGN(16);
    af_insect_runtime_end = .;
    ASSERT(. <= AF_INSECT_LIMIT,"Complete insect runtime exceeds its reservation")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
