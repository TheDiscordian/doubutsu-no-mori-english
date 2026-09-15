OUTPUT_ARCH(mips)
ENTRY(af_v3_tent_model_ct)
_Matrix_to_Mtx = 0x800E139C;
osWritebackDCache = 0x8002FE00;
SECTIONS {
    . = 0x80483400;
    .text : { *(.text.af_v3_tent_model_ct) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80483800, "Tent callback exceeds its checked code reservation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Tent callback has shared writable state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
