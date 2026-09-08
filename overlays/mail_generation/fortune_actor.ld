OUTPUT_ARCH(mips)
SECTIONS
{
    . = 0x809E5740;
    __miko_start = .;
    .text : {
        native.o(.text.native)
        __miko_adapter_start = .;
        *(.text .text.*)
        . = ALIGN(16);
    }
    __miko_text_end = .;
    .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
    __miko_end = .;
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(__miko_adapter_start == 0x809E6300, "Native Miko prefix changed")
    ASSERT(SIZEOF(.data) == 0, "New Miko code contains shared mutable data")
    ASSERT(SIZEOF(.bss) == 0, "New Miko code contains shared mutable BSS")
    ASSERT(__miko_end - __miko_start <= 8192, "Miko exceeds its native overlay pool")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
