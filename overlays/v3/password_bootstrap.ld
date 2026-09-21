OUTPUT_ARCH(mips)
ENTRY(af_v3_password_boot_check)
af_pw_dma = 0x80026B44;
af_pw_crc = 0x80195938;
af_pw_writeback = 0x8002FE00;
af_pw_invalidate = 0x80034CE0;
af_pw_fault = 0x80029AB4;
SECTIONS {
    . = 0x804B4D00;
    .text : { *(.text.af_v3_password_boot_check) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B4EF0, "Password loader overlaps its startup cache word")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected password loader state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
