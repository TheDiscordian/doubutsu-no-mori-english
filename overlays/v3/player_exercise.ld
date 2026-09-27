OUTPUT_ARCH(mips)
ENTRY(af_v3_exercise_init)
SECTIONS
{
    /* Preparation only. Native registration supplies its checked placement. */
    . = 0;
    .text : { *(.text.af_v3_exercise_init) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 8192, "Exercise core exceeds preparation budget")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected global exercise state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
