OUTPUT_ARCH(mips)
ENTRY(af_v3_room_reaction_ct)
af_rumble_motor_init = 0x80031574;
af_rumble_motor_access = 0x80031300;
af_rumble_mask = 0x8002E0E0;
af_reaction_player = 0x800B1C84;
af_reaction_shock = 0x800B2B08;
memset = 0x8003B9B0;
memcpy = 0x80034BF8;
SECTIONS {
    . = 0x804C8000;
    .text : { *(.text.af_v3_room_reaction_ct) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804CC000, "Reaction code exceeds shared room code capacity")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0, "Mutable reaction state must use its explicit reservation")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
