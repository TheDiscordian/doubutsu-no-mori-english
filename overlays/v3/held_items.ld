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
        ASSERT(. <= 0x804A6200, "Held price entry exceeds fixed slot");
        . = 0x200;
        *(.text.af_v3_held_item_icon)
        *(.text .text.*)
    }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A6800, "Held parent readers overlap pocket icon resources")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected held parent state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
