OUTPUT_ARCH(mips)
SECTIONS
{
    . = 0x8096DC30;
    __snowman_start = .;
    .text : {
        native.o(.text.native)
        __snowman_creator = .;
        *(.text .text.*)
        . = ALIGN(16);
        __snowman_code_end = .;
        native.o(.rodata.snapshots)
        . = ALIGN(16);
    }
    __snowman_end = .;
    .unexpected : { *(.rodata .rodata.* .data .data.* .bss .bss.* COMMON) }
    ASSERT(__snowman_creator == 0x80971E40, "Native Snowman prefix changed")
    ASSERT(SIZEOF(.unexpected) == 0, "Snowman creator has unexpected data or mutable state")
    ASSERT(__snowman_end - __snowman_start <= 0x6000, "Snowman actor exceeds its bounded image allocation")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
