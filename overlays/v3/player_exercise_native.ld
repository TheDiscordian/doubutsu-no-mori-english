OUTPUT_ARCH(mips)
ENTRY(af_v3_exercise_native_init)
SECTIONS {
    . = 0x804CE000;
    .text : { *(.text.af_v3_exercise_native_init) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804D0000,"Player exercise overlaps shared room code")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected player exercise global state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
