OUTPUT_ARCH(mips)
ENTRY(af_text_extension_init)
SECTIONS {
  . = 0x80D00000;
  .text : {
    *(.text.entry)
    *(.text*)
    *(.rodata*)
    *(.data*)
    . = ALIGN(16);
    *(.bss*)
    *(COMMON)
    . = ALIGN(16);
  }
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
