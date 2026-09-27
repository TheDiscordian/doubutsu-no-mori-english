OUTPUT_ARCH(mips)
ENTRY(af_v3_qd_native_bind)
SECTIONS {
    . = 0x80630000;
    .text : { *(.text.af_v3_qd_native_bind) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80636000,"Disk native code exceeds reservation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected native disk globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
