OUTPUT_ARCH(mips)
ENTRY(af_map_label_draw)
af_map_native_draw = 0x80090E98;
SECTIONS {
  . = 0x80894380;
  .text : { *(.text*) *(.rodata*) . = ALIGN(16); }
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
