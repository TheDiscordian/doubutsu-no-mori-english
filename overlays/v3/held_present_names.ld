OUTPUT_ARCH(mips)
ENTRY(af_v3_present_legacy_name)
SECTIONS
{
    . = 0x804B4480;
    .text : { *(.text.af_v3_present_legacy_name) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804B4F00, "Present name readers overlap wrapped identity table")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected present-name state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
