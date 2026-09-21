OUTPUT_ARCH(mips)
ENTRY(af_v3_password_check)
af_pw_native_random = 0x8002C9AC;
SECTIONS {
    . = 0x804C0000;
    .text : { *(.text.af_v3_password_check) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804C2800, "Password code overlaps donor tables")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected password state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
