OUTPUT_ARCH(mips)
ENTRY(af_leaflet_hour)
SECTIONS
{
    . = 0x800C4228;
    __hour_start = .;
    .text : { *(.text .text.*) }
    __hour_end = .;
    .unexpected : { *(.rodata .rodata.* .data .data.* .bss .bss.* COMMON) }
    ASSERT(SIZEOF(.unexpected) == 0, "Leaflet hour must not have data or mutable globals")
    ASSERT(__hour_end <= 0x800C42E8, "Leaflet hour exceeds the original native function")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
