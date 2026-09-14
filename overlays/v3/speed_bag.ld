OUTPUT_ARCH(mips)
ENTRY(af_v3_speed_bag_ct)
cKF_SkeletonInfo_R_ct = 0x80052228;
cKF_SkeletonInfo_R_init_standard_stop = 0x80052298;
cKF_SkeletonInfo_R_play = 0x800528D4;
cKF_Si3_draw_R_SV = 0x800530D8;
Lib_SegmentedToVirtual = 0x8009ADA8;
_Matrix_to_Mtx_new = 0x800E13C4;
/* af_v3_speed_bag_sound must be supplied by the caller. */
SECTIONS {
    /* Link origin only: text can move within KSEG0 after relocation validation. */
    . = 0x80000000;
    .text : {
        KEEP(*(.text.af_v3_speed_bag_ct))
        KEEP(*(.text.af_v3_speed_bag_mv))
        KEEP(*(.text.af_v3_speed_bag_dw))
    }
    .unsupported : { *(.text*) *(.rodata*) *(.data*) *(.bss*) *(.sdata*) *(.sbss*) *(.got*) }
    ASSERT(SIZEOF(.unsupported) == 0, "unexpected speed-bag code/data dependency")
    ASSERT(SIZEOF(.text) <= 0x400, "speed-bag callback text exceeds reservation")
    /DISCARD/ : { *(.comment) *(.note*) *(.MIPS.abiflags) *(.reginfo) *(.pdr) *(.gnu.attributes) }
}
