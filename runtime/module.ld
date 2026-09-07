OUTPUT_ARCH(mips)
ENTRY(af_runtime_init)
SECTIONS
{
    . = 0x801948E0;
    __module_start = .;
    .header : { KEEP(*(.module_header)) }
    . = __module_start + 0x100;
    .watchdog : { KEEP(*(.watchdog)) }
    ASSERT(SIZEOF(.watchdog) == 0x1F0, "Watchdog size mismatch")
    . = __module_start + 0x300;
    .init : { KEEP(*(.text.af_runtime_init)) }
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    . = ALIGN(16);
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    __module_end = .;
    __module_used = __module_end - __module_start;
    ASSERT(__module_end <= __module_start + 0x6000, "Translation module reaches native-test scratch RAM")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
