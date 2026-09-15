OUTPUT_ARCH(mips)
ENTRY(af_v3_camper_greeting)
native_private = 0x80136FD8;
native_hour = 0x80136FBE;
camper_last_gift = 0x804A1A12;
native_looks = 0x800AD084;
native_first = 0x8092CD5C;
native_winter = 0x8092D808;
native_ordinary = 0x8092D4D0;
native_random = 0x8002C9AC;
native_item_kind = 0x80468000;
SECTIONS {
    . = 0x8092DAE0;
    .text : { *(.text.af_v3_camper_greeting) *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x8092ED00, "Summer greetings exceed checked shared conversation storage")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "No implicit summer greeting state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
