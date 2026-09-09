OUTPUT_ARCH(mips)
ENTRY(af_free_boot_tail)
SECTIONS {
  .text.tail 0x800D65D0 : { *(.text.tail) }
  .text.letter 0x80919C68 : { *(.text.letter) }
  .text.reserve 0x80A09438 : { *(.text.reserve) }
  .text.shrine 0x80A0AA6C : { *(.text.shrine) }
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
af_boot_failed = 0x800D65BC;
