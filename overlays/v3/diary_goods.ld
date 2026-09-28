OUTPUT_ARCH(mips)
ENTRY(af_v3_goods_ctor)
af_goods_fg2 = 0x8008AA98;
af_goods_writeback = 0x8002FE00;
Matrix_RotateY = 0x800E0698;
Matrix_scale = 0x800E041C;
memset = 0x8003B9B0;
memcpy = 0x80034BF8;
SECTIONS {
 . = 0x806E0800;
 .text : { *(.text.af_v3_goods_ctor) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Room drawing uses its existing lifetime state")
 ASSERT(. <= 0x806E2000, "Room adapter exceeds diary packet reservation")
}
