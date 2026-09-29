OUTPUT_ARCH(mips)
ENTRY(af_hp_descriptor)
SECTIONS {
 . = DEFINED(AF_HP_LINK_RAM) ? AF_HP_LINK_RAM : 0x8073C010;
 af_hp_packet_start = .;
 .text : { *(.text .text.*) . = ALIGN(16); }
 af_hp_code_end = .;
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .data : { *(.data .data.*) . = ALIGN(16); }
 af_hp_bss_start = .;
 .bss : { *(.bss .bss.* COMMON) . = ALIGN(16); }
 af_hp_bss_end = .;
 /* Include BSS in the cartridge packet so startup initializes all state. */
 .guard : { LONG(0x41464850); LONG(0x41464850); LONG(0x41464850); LONG(0x41464850); }
 af_hp_packet_end = .;
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(. <= 0x807DA800, "Participants exceed checked resident memory")
}
