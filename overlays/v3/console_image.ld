OUTPUT_ARCH(mips)
ENTRY(af_v3_console_load_image)
SECTIONS {
  . = 0;
  .text : { *(.text.af_v3_console_load_image) *(.text*) }
  .rodata : { *(.rodata*) }
  .data : { *(.data*) *(.sdata*) }
  .bss (NOLOAD) : { *(.bss*) *(.sbss*) *(COMMON) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) *(.MIPS.abiflags) *(.reginfo) *(.pdr) }
  ASSERT(SIZEOF(.data) == 0, "Console loader has mutable globals")
  ASSERT(SIZEOF(.bss) == 0, "Console loader has unallocated BSS")
  ASSERT(. <= 0x2000, "Console image loader exceeds code budget")
}
