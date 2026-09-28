OUTPUT_ARCH(mips)
ENTRY(af_v3_roster_clothing_record)
SECTIONS
{
    . = 0x8066E000;
    .text : { *(.text.af_v3_roster_clothing_record) *(.text .text.*) }
    ASSERT(. <= 0x8066E800, "Clothing code overlaps complete category records")
    . = 0x8066E800;
    .rodata : { KEEP(*(.rodata.clothing_records)) *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8066EFF0, "Clothing category overlaps guard")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0, "Clothing category has unexpected state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
