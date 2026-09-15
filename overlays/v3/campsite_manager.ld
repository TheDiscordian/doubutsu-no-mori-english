OUTPUT_ARCH(mips)
ENTRY(af_v3_camper_event_start)
camper = 0x804A1A00;
native_installed = 0x8019ACD0;
selected_furniture = 0x80484000;
native_event_index = 0x804A2B00;
native_today = 0x80139F98;
native_changes = 0x80104F9C;
selected_villager = 0x804634B0;
native_event = 0x800AA14C;
af_v3_camper_register = 0x804A2D00;
af_v3_campsite_choose = 0x804A2478;
native_field_valid = 0x80087C40;
native_field_id = 0x80087C88;
native_get_save = 0x8008033C;
native_reserve_save = 0x80080080;
native_clear_save = 0x800804AC;
native_check_keep = 0x80080040;
native_set_keep = 0x8007FFC4;
native_clear_keep = 0x80080000;
native_set_status = 0x8007FDA8;
native_clear_status = 0x8007FE74;
native_reset_appeared = 0x800AA49C;
native_shuffle = 0x800A6810;
native_unseen = 0x800AA3A4;
native_grow = 0x800AD6D4;
native_mark_appeared = 0x800AA2F8;
native_get_place = 0x80080D68;
native_get_fg = 0x8008A670;
native_place_tent = 0x8095D324;
native_remove_tent = 0x8095D1E0;
SECTIONS {
    . = 0x80964DA0;
    .text : { *(.text.af_v3_camper_event_start) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x809670B0, "Camper manager exceeds reviewed on-demand bound")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "No implicit camper manager state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
