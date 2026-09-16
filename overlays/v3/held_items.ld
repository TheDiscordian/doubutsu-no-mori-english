OUTPUT_ARCH(mips)
ENTRY(af_v3_held_item_name)
SECTIONS
{
    . = 0x804A6000;
    .text : {
        *(.text.af_v3_held_item_name)
        ASSERT(. <= 0x804A6100, "Held name entry exceeds fixed slot");
        . = 0x100;
        *(.text.af_v3_held_item_price)
        *(.text .text.*)
    }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A7000, "Held parent readers overlap action tables")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected held parent state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
