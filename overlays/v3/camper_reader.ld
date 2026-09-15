OUTPUT_ARCH(mips)
ENTRY(af_v3_camper_npc_info)
camper = 0x804A1A00;
native_installed = 0x8019ACD0;
native_event = 0x800AA14C;
original_npc_info = 0x804A1F60;
SECTIONS {
    . = 0x804A29A0;
    .text : { *(.text.af_v3_camper_npc_info) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A2B00, "Camper reader overlaps calendar index")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Camper has an explicit owner")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
