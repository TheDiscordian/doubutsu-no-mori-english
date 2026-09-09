OUTPUT_ARCH(mips)
ENTRY(af_letter_header)
INCLUDE imports.ld
SECTIONS {
  . = 0x80888E90;
  .text : {
    *(.native)
    __letter_names_code_start = .;
    *(.text*)
    __letter_names_code_end = .;
    *(.rodata*)
    . = ALIGN(16);
    __letter_names_bss_start = .;
    __letter_names_end = .;
  }
  .forbidden : { *(.bss*) *(COMMON) *(.data*) *(.sdata*) *(.sbss*) }
  ASSERT(SIZEOF(.forbidden) == 0, "Letter names must not add mutable storage")
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
