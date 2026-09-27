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
sAdo_SysTrgStart = 0x800D1A9C;
sAdo_OngenPos = 0x800D1D08;
_Matrix_to_Mtx = 0x800E139C;
osWritebackDCache = 0x8002FE00;
sqrtf = 0x80033470;
af_v3_fire_before = 0x80483810;
af_v3_fire_after = 0x80483B00;
af_effect_random = 0x8002C9AC;
Matrix_translate = 0x800E0314;
Matrix_mult = 0x800E02BC;
Matrix_scale = 0x800E041C;
_texture_z_light_fog_prim_xlu = 0x800BD598;
_texture_z_light_fog_prim = 0x800BD4E8;
Matrix_RotateY = 0x800E0698;
qrand = 0x8002C970;
sin_s = 0x80099A94;
add_calc = 0x8009A570;
cos_s = 0x80099A54;
af_v3_room_debug = 0x80138E50;
af_rumble_motor_init = 0x80031574;
af_rumble_motor_access = 0x80031300;
af_rumble_mask = 0x8002E0E0;
af_reaction_player = 0x800B1C84;
af_reaction_shock = 0x800B2B08;
memset = 0x8003B9B0;
memcpy = 0x80034BF8;
gfx_set_fog_nosync = 0x800BD37C;
mFI_GetFieldId = 0x80087C88;
mHS_get_arrange_idx = 0x80094BF4;
mBGMPsComp_make_ps_room = 0x8005E0DC;
mBGMPsComp_delete_ps_room = 0x8005E69C;
mBGMPsComp_MDPlayerPos_make = 0x8005EA24;
mBGMPsComp_MDPlayerPos_delete = 0x8005EA38;
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
