OUTPUT_ARCH(mips)
ENTRY(af_v3_goods_ctor)
af_goods_fg2 = 0x8008AA98;
Matrix_RotateY = 0x800E0698;
Matrix_scale = 0x800E041C;
memset = 0x8003B9B0;
memcpy = 0x80034BF8;
SECTIONS {
    . = 0x804D9000;
    .text : { *(.text.af_v3_goods_ctor) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804DA000,"Loose-item adapters exceed their code reservation")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0,"Unexpected loose-item adapter state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
