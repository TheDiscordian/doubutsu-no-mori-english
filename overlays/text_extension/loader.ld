OUTPUT_ARCH(mips)
ENTRY(af_text_extension_boot)
SECTIONS {
  . = 0x8009D6D0;
  .text : { *(.text*) }
  ASSERT(. <= 0x8009D820, "Text-extension loader exceeds the native free-setter span")
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
