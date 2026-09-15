OUTPUT_ARCH(mips)
ENTRY(af_v3_camper_movein_candidate)
native_installed = 0x8019ACD0;
native_event_save = 0x8008033C;
native_animal_search = 0x800A7C30;
native_animal_free = 0x800A7AEC;
SECTIONS {
    . = 0x80463EE0;
    .text : { *(.text.af_v3_camper_movein_candidate) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80464000, "Camper move-in guards overlap the shared villager reader")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Camper move-in guards have no implicit state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
