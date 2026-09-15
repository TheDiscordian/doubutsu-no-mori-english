OUTPUT_ARCH(mips)
ENTRY(af_v3_tent_model_ct)
_Matrix_to_Mtx = 0x800E139C;
osWritebackDCache = 0x8002FE00;
af_v3_legacy_tent_layout = 0x80483740;
SECTIONS {
    . = 0x80483400;
    .text : {
        *(.text.af_v3_tent_model_ct)
        *(.text.af_v3_tent_model_dt)
        *(.text.draw .text.draw.*)
        *(.text.layout_entry)
        ASSERT(. <= 0x300, "Shared palette callback exceeds its code reservation");
        . = 0x360;
        *(.text.af_v3_tent_model_mv)
    }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80483800, "Shared palette entries exceed the existing tent reservation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Shared palette callback has writable state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
