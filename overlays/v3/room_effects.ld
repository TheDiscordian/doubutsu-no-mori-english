/* Standalone preparation address, not an additional resident reservation.
 * Installation links these callbacks into the existing shared room packet.
 */
OUTPUT_ARCH(mips)
ENTRY(af_v3_flash_init)
af_effect_random = 0x8002C9AC;
Matrix_translate = 0x800E0314;
Matrix_mult = 0x800E02BC;
Matrix_scale = 0x800E041C;
_Matrix_to_Mtx = 0x800E139C;
osWritebackDCache = 0x8002FE00;
_texture_z_light_fog_prim_xlu = 0x800BD598;
_texture_z_light_fog_prim = 0x800BD4E8;
Matrix_RotateY = 0x800E0698;
Lib_SegmentedToVirtual = 0x8009ADA8;
qrand = 0x8002C970;
sin_s = 0x80099A94;
cos_s = 0x80099A54;
af_v3_room_debug = 0x80138E50;
sAdo_OngenTrgStart = 0x800D1D58;
SECTIONS {
    . = 0x804C8000;
    .text : { *(.text.af_v3_flash_init) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804CC000, "Effect preparation exceeds shared packet code capacity")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Effect callbacks have shared writable state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
