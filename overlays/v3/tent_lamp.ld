OUTPUT_ARCH(mips)
ENTRY(af_v3_lamp_ct)
af_v3_lamp_state = 0x8046FFC0;
native_scene = 0x80126EB4;
native_seconds = 0x80136FB8;
native_effect_loaded = 0x801010C0;
native_malloc = 0x8009BFC0;
native_free = 0x8009C040;
native_dma = 0x80026B44;
native_writeback = 0x8002FE00;
native_approach = 0x8009A570;
native_opaque_state = 0x800BD5E8;
native_environment_continue = 0x800984D4;
native_room_prim_continue = 0x800981C0;
native_set_diffuse = 0x8009802C;
native_permit_diffuse = 0x80098158;
SECTIONS {
    . = 0x8046E000;
    .text : { KEEP(*(.entry)) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8046FFC0, "Tent lamp code overlaps explicit state")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "No implicit lamp state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
