OUTPUT_ARCH(mips)
ENTRY(af_v3_room_scroll_dw)
_Matrix_to_Mtx = 0x800E139C;
osWritebackDCache = 0x8002FE00;
af_v3_room_debug = 0x80138E50;
sAdo_OngenPos = 0x800D1D08;
sAdo_OngenTrgStart = 0x800D1D58;
SECTIONS {
    . = 0x804BA000;
    .text : { *(.text.af_v3_room_scroll_dw) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804BB000, "Room scroll code overlaps its records")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected shared scroll state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
