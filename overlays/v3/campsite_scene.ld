OUTPUT_ARCH(mips)
ENTRY(af_v3_campsite_scene_status)
SECTIONS {
    . = 0x804A0100;
    .text : { KEEP(*(.entry)) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss : { *(.bss .bss.* COMMON) }
    ASSERT(SIZEOF(.data) == 0, "Campsite scene callbacks require no writable globals")
    ASSERT(SIZEOF(.bss) == 0, "Campsite scene callbacks require no BSS")
    ASSERT(. <= 0x804A1000, "Campsite scene code overlaps its data packet")
    /DISCARD/ : { *(.comment) *(.note*) *(.MIPS.abiflags) *(.reginfo) *(.pdr) *(.gnu.attributes) }
}
