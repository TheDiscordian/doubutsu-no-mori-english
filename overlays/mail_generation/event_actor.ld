OUTPUT_ARCH(mips)
SECTIONS
{
    . = 0x8095B8B0;
    __event_start = .;
    .text : {
        native.o(.text.native)
        __event_creator = .;
        native.o(.text.creator)
        __event_adapter = .;
        *(.text .text.*)
        . = ALIGN(16);
        __event_text_end = .;
        *(.rodata .rodata.* .data .data.* .bss .bss.* COMMON)
        . = ALIGN(16);
    }
    __event_end = .;
    ASSERT(__event_creator == 0x80962460, "Original event file/BSS bounds changed")
    ASSERT(__event_end - __event_start <= 0xC000, "Event actor exceeds guarded heap image budget")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
