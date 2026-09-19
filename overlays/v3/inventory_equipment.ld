OUTPUT_ARCH(mips)
ENTRY(af_v3_inventory_item_kind)
SECTIONS
{
    . = 0x804A9000;
    .text : { *(.text.af_v3_inventory_item_kind) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A9400, "Inventory equipment code overlaps lookup tables")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected inventory equipment state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
