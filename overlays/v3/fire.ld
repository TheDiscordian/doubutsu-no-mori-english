OUTPUT_ARCH(mips)
ENTRY(af_v3_campfire_ct)
cKF_SkeletonInfo_R_ct = 0x80052228;
cKF_SkeletonInfo_R_init_standard_repeat = 0x80052408;
cKF_SkeletonInfo_R_play = 0x800528D4;
cKF_Si3_draw_R_SV = 0x800530D8;
Lib_SegmentedToVirtual = 0x8009ADA8;
sAdo_OngenPos = 0x800D1D08;
Matrix_Position_Zero = 0x800E14D4;
Matrix_push = 0x800E020C;
Matrix_pull = 0x800E0244;
Matrix_translate = 0x800E0314;
Matrix_mult = 0x800E02BC;
Matrix_RotateY = 0x800E0698;
Matrix_scale = 0x800E041C;
_Matrix_to_Mtx = 0x800E139C;
osWritebackDCache = 0x8002FE00;
SECTIONS {
    . = 0x80483800;
    .text : { *(.text.af_v3_campfire_ct) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x80483D00, "Fire callbacks overlap shared furniture behaviour code")
    ASSERT(SIZEOF(.rodata) <= 4, "Fire callbacks contain unexpected constant data")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Fire callbacks have shared writable state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
