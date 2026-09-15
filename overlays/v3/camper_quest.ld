OUTPUT_ARCH(mips)
ENTRY(af_v3_camper_profile)
camper_greeted = 0x804A1A10;
SECTIONS {
    . = 0x804A2EC0;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804A2FF0, "Camper quest adapters overlap the package guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Camper state has an existing owner")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
