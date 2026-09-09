OUTPUT_ARCH(mips)
ENTRY(af_map_init)
INCLUDE imports.ld
SECTIONS {
  . = 0x8088DBD0;
  .text : {
    *(.native)
    __map_code_start = .;
    *(.text*)
    __map_code_end = .;
    *(.rodata*)
    . = ALIGN(16);
    __map_bss_start = .;
    *(.bss*)
    *(COMMON)
    . = ALIGN(16);
    __map_end = .;
  }
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
