OUTPUT_ARCH(mips)
ENTRY(af_guide_name)
SECTIONS {
  . = 0x809CA3B0;
  .text : { *(.text.guide_name) }
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
