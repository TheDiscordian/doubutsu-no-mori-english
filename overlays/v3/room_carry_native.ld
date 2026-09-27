OUTPUT_ARCH(mips)
ENTRY(af_v3_carry_ctor)
af_carry_ground = 0x80071B78;
Matrix_RotateY = 0x800E0698;
sin_s = 0x80099A94;
cos_s = 0x80099A54;
memset = 0x8003B9B0;
memcpy = 0x80034BF8;
/* Installed goods addresses are supplied by checked compiler definitions. */
SECTIONS {
    . = 0x804DA000;
    .text : { *(.text.af_v3_carry_ctor) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804DC000,"Native carrying code overlaps loose-item state")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected native carrying state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
