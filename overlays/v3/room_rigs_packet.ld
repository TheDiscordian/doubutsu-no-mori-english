OUTPUT_ARCH(mips)
ENTRY(af_v3_room_rig_ct)
cKF_SkeletonInfo_R_ct = 0x80052228;
cKF_SkeletonInfo_R_init_standard_stop = 0x80052298;
cKF_SkeletonInfo_R_init_standard_repeat = 0x80052408;
cKF_SkeletonInfo_R_play = 0x800528D4;
cKF_Si3_draw_R_SV = 0x800530D8;
Lib_SegmentedToVirtual = 0x8009ADA8;
_Matrix_to_Mtx_new = 0x800E13C4;
sAdo_OngenTrgStart = 0x800D1D58;
sAdo_OngenPos = 0x800D1D08;
_Matrix_to_Mtx = 0x800E139C;
osWritebackDCache = 0x8002FE00;
sqrtf = 0x80033470;
af_v3_fire_before = 0x80483810;
af_v3_fire_after = 0x80483B00;
SECTIONS {
    . = DEFINED(AF_ROOM_ORIGIN) ? AF_ROOM_ORIGIN : 0x804B8000;
    .text : { *(.text.af_v3_room_rig_ct) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= (DEFINED(AF_ROOM_CODE_LIMIT) ? AF_ROOM_CODE_LIMIT : 0x804B9000), "Room rig code overlaps its records")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected shared room-rig state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
