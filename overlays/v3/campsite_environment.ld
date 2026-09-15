OUTPUT_ARCH(mips)
ENTRY(af_v3_campsite_floor)
native_scene = 0x80126EB4;
native_field_draw = 0x80136EA2;
native_floor_body = 0x800BEECC;
native_point_body = 0x80096D68;
SECTIONS {
    . = 0x804A2F54;
    .text : SUBALIGN(4) { *(.text.environment) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A2FF0, "Campsite environment overlaps package guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Environment bindings have no implicit state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
