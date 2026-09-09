OUTPUT_ARCH(mips)
SECTIONS {
  .text.preparation 0x80A963E8 : { *(.text.preparation) }
  .text.length 0x80A9642C : { *(.text.length) }
  .text.identity 0x800AD050 : { *(.text.identity) }
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
