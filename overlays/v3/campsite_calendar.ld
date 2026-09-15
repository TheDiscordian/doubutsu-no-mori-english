OUTPUT_ARCH(mips)
ENTRY(af_v3_campsite_today_init)
campsite_index = 0x804A2B00;
campsite_calendar = 0x804A2C40;
native_rtc = 0x80136FBE;
selected_furniture = 0x80484000;
native_scene = 0x80126EB4;
native_last_scene = 0x80136EA4;
native_game = 0x8010EF90;
native_today_init = 0x8007E60C;
native_first_enter = 0x8007F2D8;
native_add_today = 0x8007E264;
native_one_time = 0x8007F28C;
native_decode_date = 0x8007F1A8;
af_v3_campsite_schedule = 0x804A2100;
SECTIONS {
    . = 0x804A2740;
    .text : { *(.text.af_v3_campsite_today_init) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A2B00, "Campsite calendar overlaps its event index")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Calendar state needs explicit ownership")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
