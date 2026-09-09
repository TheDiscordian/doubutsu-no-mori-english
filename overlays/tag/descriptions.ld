OUTPUT_ARCH(mips)
ENTRY(af_tag_description_hook)
INCLUDE imports.ld
SECTIONS {
  . = 0x8086F310;
  .text : {
    *(.native_head)
    __description_lines_start = .;
    *(.description_lines)
    __description_lines_end = .;
    ASSERT(. <= 0x80877EC4, "English segment drawer exceeds replaced Japanese drawer");
    . = 0x8BB4;
    *(.native_tail)
    __description_start = .;
    *(.description_hook)
    *(.quest_names)
    *(.text*)
    __description_code_end = .;
    *(.rodata*)
    . = ALIGN(16);
    *(.bss*)
    *(COMMON)
    . = ALIGN(16);
    __description_end = .;
  }
  /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) *(.gnu.attributes) }
}
