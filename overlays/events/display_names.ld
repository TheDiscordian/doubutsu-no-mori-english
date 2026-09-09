OUTPUT_ARCH(mips)
SECTIONS {
  .text.call 0x809DFF2C : { *(.text.call) }
  .text.length 0x809DFF44 : { *(.text.length) }
  .text.reserve_name 0x80A09458 : { *(.text.reserve_name) }
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
reserve_resume = 0x80A09484;
