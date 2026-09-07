OUTPUT_ARCH(mips)
SECTIONS
{
    . = 0x80A94AC0;
    .text : { entry.o(.text) . = ALIGN(16); grade.o(.text) . = ALIGN(16); prefixes.o(.text) . = ALIGN(16); }
    _af_mail_checkSegmentTextSize = SIZEOF(.text);
    .data : { entry.o(.data) . = ALIGN(16); grade.o(.data) . = ALIGN(16); prefixes.o(.data) . = ALIGN(16); }
    _af_mail_checkSegmentDataSize = SIZEOF(.data);
    .rodata : { entry.o(.rodata) . = ALIGN(16); grade.o(.rodata) . = ALIGN(16); prefixes.o(.rodata) . = ALIGN(16); }
    _af_mail_checkSegmentRoDataSize = SIZEOF(.rodata);
    .bss (NOLOAD) : { entry.o(.bss) grade.o(.bss) prefixes.o(.bss) }
    _af_mail_checkSegmentBssSize = SIZEOF(.bss);
    af_mail_check_end = .;
    ASSERT(af_mail_legacy_entry == 0x80A94D0C, "Native mail-check entry moved")
    ASSERT(af_mail_check_end <= 0x80A96170, "Mail checker exceeds original allocation")
    ASSERT(SIZEOF(.bss) == 0, "Mail checker must not retain mutable state")
    .ovl : { relocation.o(.ovl) }
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
