OUTPUT_ARCH(mips)
ENTRY(af_mail_generate)
SECTIONS
{
    . = 0x80200000;
    __probe_start = .;
    .text : { *(.text .text.*) }
    __probe_end = .;
    .unexpected : { *(.rodata .rodata.* .data .data.* .bss .bss.* COMMON) }
    ASSERT(SIZEOF(.unexpected) == 0, "Generation probe must not need data relocation or mutable globals")
    ASSERT(__probe_end - __probe_start <= 0x1000, "Generation probe exceeds its code budget")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
