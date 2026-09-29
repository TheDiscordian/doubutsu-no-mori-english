OUTPUT_ARCH(mips)
ENTRY(af_v3_console_storage_reset)
SECTIONS {
 . = AF_HI_STORAGE_RAM;
 .text : { *(.text.af_v3_console_storage_reset) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden)==0, "Event profile storage retains existing state and scratch")
 ASSERT(. <= AF_HI_STORAGE_RAM+0x4000, "Event profile storage exceeds its reservation")
}
