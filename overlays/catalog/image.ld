OUTPUT_ARCH(mips)
ENTRY(af_catalog_init)
INCLUDE imports.ld
SECTIONS {
  . = 0x808A6100;
  .text : {
    *(.native)
    __catalog_code_start = .;
    *(.text*)
    __catalog_code_end = .;
    *(.rodata*)
    . = ALIGN(16);
    __catalog_bss_start = .;
    *(.bss*)
    *(COMMON)
    . = ALIGN(16);
    __catalog_end = .;
  }
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
