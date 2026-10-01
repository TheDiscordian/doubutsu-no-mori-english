OUTPUT_ARCH(mips)
ENTRY(af_v3_travel_passport_save)
SECTIONS {
 .io 0x806A4800 : {
   pak_native.o(.text .text.* .rodata .rodata.* .data .data.*)
   pak_codec.o(.text .text.* .rodata .rodata.* .data .data.*)
   pak_workspace.o(.text .text.* .rodata .rodata.* .data .data.*)
   console_storage.o(.text .text.* .rodata .rodata.* .data .data.*)
   . = ALIGN(16);
   af_travel_harvest_crc = .; LONG(0);
   af_travel_record_crc = .; LONG(0);
   . = ALIGN(16);
 }
 .io_bss : {
   pak_native.o(.bss .bss.* COMMON) pak_codec.o(.bss .bss.* COMMON)
   pak_workspace.o(.bss .bss.* COMMON) console_storage.o(.bss .bss.* COMMON)
 }
 ASSERT(SIZEOF(.io_bss) == 0, "Pak workspace may not acquire private BSS")
 ASSERT(ADDR(.io) + SIZEOF(.io) <= 0x806A7FF0, "Pak code exceeds diary padding")
 .life 0x807F7B50 : {
   travel_native.o(.text .text.* .rodata .rodata.* .data .data.*)
   travel_player.o(.text .text.* .rodata .rodata.* .data .data.*)
   travel_context.o(.text .text.* .rodata .rodata.* .data .data.*)
   . = ALIGN(16);
   /* Explicit loaded zero data, not an uninitialised heap/BSS allocation. */
   BYTE(0); . = ALIGN(16);
   travel_native.o(.bss .bss.* COMMON)
   travel_player.o(.bss .bss.* COMMON) travel_context.o(.bss .bss.* COMMON)
   . = ALIGN(16);
 }
 ASSERT(ADDR(.life) + SIZEOF(.life) <= 0x807FC000, "Player lifecycle exceeds Harvest padding")
 .forbidden : { *(.text .text.* .rodata .rodata.* .data .data.* .bss .bss.* COMMON) }
 ASSERT(SIZEOF(.forbidden) == 0, "Unassigned travelling-player code or state")
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
}
