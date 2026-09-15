OUTPUT_ARCH(mips)
ENTRY(af_v3_camper_pocket)
native_private = 0x80136FD8;
native_trade_state = 0x80921DE8;
native_scene = 0x80126EB4;
camper_last_gift = 0x804A1A12;
native_rare_item = 0x80135C00;
native_random = 0x8002C9AC;
native_item_kind = 0x80468000;
native_house_item = 0x800ABAA8;
native_random_goods = 0x800BFCF0;
native_goods_priority = 0x800C1BF0;
native_item_name = 0x800BB6A0;
native_other_fruit = 0x8008D6E0;
native_trade_body = 0x8091EFE4;
SECTIONS {
    . = 0x80922370;
    .text : { *(.text.af_v3_camper_pocket) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80925000, "Camper trades exceed checked shared conversation storage")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "No implicit camper trade state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
