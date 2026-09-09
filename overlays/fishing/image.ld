OUTPUT_ARCH(mips)
ENTRY(af_fishing_name)
af_fishing_native_set = 0x8009D6D0;
SECTIONS {
  . = 0x80A8FCF0;
  .text : {
    *(.native)
    __fishing_code_start = .;
    *(.text*)
    __fishing_code_end = .;
    *(.rodata*)
    *(.aliases)
    . = ALIGN(16);
    __fishing_end = .;
  }
  .forbidden : { *(.bss*) *(COMMON) *(.data*) *(.sdata*) *(.sbss*) }
  ASSERT(SIZEOF(.forbidden) == 0, "Fishing helper must not add mutable storage")
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
