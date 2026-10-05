OUTPUT_ARCH(mips)
ENTRY(af_bank_mail_start)
SECTIONS {
    /DISCARD/ : { *(.text.af_mail_record_unpack) *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
    . = 0x807E8040;
    .text : { *(.text.af_bank_mail_start) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x807E8FF0,"Savings mail overlaps Nook's retained title buffer")
    ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Unexpected savings mail state")
}
