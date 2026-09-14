OUTPUT_ARCH(mips)
ENTRY(af_v3_hra_remaining)
af_v3_room_query = 0x804680B8;
af_v3_furniture_import_profile = 0x80465000;
SECTIONS
{
    /* Preserve every existing code/data/BSS address in the translated owner. */
    . = 0x80929C30;
    .text : { *(.text.af_v3_hra_remaining) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8092D9E0, "V3 HRA owner exceeds its 32-KiB image bound")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected HRA suffix state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
