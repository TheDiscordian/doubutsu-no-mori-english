OUTPUT_ARCH(mips)
ENTRY(af_v3_creature_passport_save)
af_pak_set_kind = 0x8007919C;
af_pak_read = 0x800792FC;
af_pak_write = 0x8007920C;
af_pak_check_private = 0x800B7F78;
af_pak_clear_private = 0x800B7ADC;
af_pak_clear_animal = 0x800A7A04;
af_creature_item_type = AF_CREATURE_ITEM_TYPE;
af_creature_save_collect = AF_CREATURE_SAVE_COLLECT;
af_v3_require_save_state = AF_CREATURE_REQUIRE_STATE;
af_v3_save_halt = AF_CREATURE_SAVE_HALT;
af_v3_creature_profile_byte = 0x80654000;
SECTIONS {
    . = 0x80655000;
    .text : { *(.text.af_v3_creature_passport_save) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80655FC0,"Creature travel overlaps visitor state")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected creature travel globals")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
