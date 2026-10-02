OUTPUT_ARCH(mips)
ENTRY(af_v3_freshwater_swim)
SECTIONS {
    . = 0x80653920;
    .text : {
        *(.text.af_v3_freshwater_swim)
        *(.text.speed .text.uki .text.af_v3_freshwater_swim_init)
        *(.text.af_v3_freshwater_wait_init .text.af_v3_freshwater_escape_init)
        *(.text.af_v3_freshwater_wait .text)
        af_fresh_main_end = .;
        ASSERT(. <= 0x80653FF0,"Freshwater swimming overlaps creature profiles");
        . = 0x1250;
        af_fresh_tail_start = .;
        *(.text.af_v3_freshwater_escape)
    }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    af_fresh_tail_end = .;
    ASSERT(. <= 0x80654EF0,"Freshwater escape overlaps the collection UI identity table")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected freshwater movement globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
