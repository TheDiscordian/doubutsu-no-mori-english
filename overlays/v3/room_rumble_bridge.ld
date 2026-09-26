OUTPUT_ARCH(mips)
ENTRY(af_v3_room_rumble_bridge)
SECTIONS {
    . = 0x800B11B8;
    .text : {
        *(.text.af_v3_room_rumble_bridge)
        ASSERT(. <= 0x800B11F8, "Rumble entry exceeds replaced player-size tail");
        . = 0x16C;
        *(.text.af_v3_room_rumble_ready)
        *(.text .text.*)
    }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x800B1364, "Rumble guard exceeds replaced equipment-size tail")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0, "Unexpected rumble bridge state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
