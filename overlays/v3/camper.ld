OUTPUT_ARCH(mips)
ENTRY(af_v3_camper_register)
camper = 0x804A1A00;
native_installed = 0x8019ACD0;
native_event = 0x800AA14C;
native_free_event = 0x800A9F9C;
native_register = 0x800AA028;
selected_villager = 0x804634B0;
selected_outfit = 0x80473BAC;
native_clear_animal = 0x800A7A04;
native_set_index = 0x800AD8C4;
native_set_memory = 0x800A71F8;
native_private = 0x80136FD8;
SECTIONS {
    . = 0x804A2D00;
    .text : { *(.text.af_v3_camper_register) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A2FF0, "Camper registration overlaps package guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Camper has an explicit owner")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
