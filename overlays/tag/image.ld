OUTPUT_ARCH(mips)
ENTRY(af_tag_cells)
SECTIONS {
  . = 0x8086F310;
  .text : {
    *(.native)
    __tag_code_start = .;
    *(.text*)
    __tag_code_end = .;
    *(.rodata*)
    *(.labels)
    . = ALIGN(16);
    __tag_end = .;
  }
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
