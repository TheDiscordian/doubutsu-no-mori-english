OUTPUT_ARCH(mips)
ENTRY(af_v3_campsite_actor_descriptor)
campsite_actor_packet = 0x804A1800;
native_descriptors = 0x80100C90;
selected_furniture = 0x80484000;
native_seconds = 0x80136FB8;
native_scene = 0x80126EB4;
native_exit = 0x80137608;
native_malloc = 0x8009BFC0;
native_free = 0x8009C040;
native_dma = 0x80026B44;
native_delete = 0x800567E8;
native_fg = 0x8008AA24;
native_get_fg = 0x8008A5A0;
native_clear_snowman = 0x800C8828;
native_unbury = 0x800A5A0C;
native_keep = 0x800B61E8;
native_deposit_off = 0x8008C6AC;
native_height = 0x80073D80;
native_ground = 0x80071B78;
native_player = 0x800B1C84;
native_block = 0x80088710;
native_demo = 0x8007CF00;
native_request_door = 0x800B27B0;
native_goto = 0x800C6C10;
native_bgm = 0x8005DDE4;
native_make = 0x80057E24;
native_matrix = 0x800E139C;
native_writeback = 0x8002FE00;
native_opaque_state = 0x800BD5E8;
native_shadow_state = 0x800BD510;
SECTIONS {
    . = 0x804A0360;
    .text : { *(.entry) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A1000, "Campsite exterior code reservation exceeded")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Campsite exterior has shared writable state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
