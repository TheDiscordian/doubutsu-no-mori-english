OUTPUT_ARCH(mips)
ENTRY(af_v3_private_bank_init)
SECTIONS {
    . = 0x804F3100;
    .text : { *(.text.af_v3_private_bank_init) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804F4980,"Private bank code exceeds retired scratch reservation")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected private bank code state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
