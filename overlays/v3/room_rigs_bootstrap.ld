OUTPUT_ARCH(mips)
ENTRY(af_v3_room_boot_ct)
af_room_dma = 0x80026B44;
af_room_crc = 0x80195938;
af_room_writeback = 0x8002FE00;
af_room_invalidate = 0x80034CE0;
af_room_fault = 0x80029AB4;
SECTIONS {
    . = 0x804B1800;
    .text : { *(.text.af_v3_room_boot_ct) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B1E00, "Room bootstrap overlaps its startup cache word")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected room-bootstrap state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
