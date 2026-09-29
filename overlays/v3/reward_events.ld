OUTPUT_ARCH(mips)
ENTRY(af_hp_descriptor)
SECTIONS {
 . = 0x807CD040;
 af_hp_packet_start = .;
 .text : { *reward-events.o(.text .text.*) . = ALIGN(16); }
 af_hp_code_end = .;
 .rodata : { *reward-events.o(.rodata .rodata.*) . = ALIGN(16); }
 .data : { *reward-events.o(.data .data.*) . = ALIGN(16); }
 af_hp_bss_start = .;
 .bss : { *reward-events.o(.bss .bss.* COMMON) . = ALIGN(16); }
 af_hp_bss_end = .;
 .guard : { LONG(0x41464850); LONG(0x41464850); LONG(0x41464850); LONG(0x41464850); }
 af_hp_packet_end = .;
 ASSERT(. <= 0x807D4040, "Golden reward actors exceed their reservation")
 . = 0x807D4040;
 af_rw_effect_packet_start = .;
 .effects_text : { *reward-effects.o(.text .text.*) . = ALIGN(16); }
 af_rw_effect_code_end = .;
 .effects_rodata : { *reward-effects.o(.rodata .rodata.*) . = ALIGN(16); }
 .effects_data : { *reward-effects.o(.data .data.*) . = ALIGN(16); }
 af_rw_effect_bss_start = .;
 .effects_bss : { *reward-effects.o(.bss .bss.* COMMON) . = ALIGN(16); }
 af_rw_effect_bss_end = .;
 .effects_guard : { LONG(0x41465257); LONG(0x41465257); LONG(0x41465257); LONG(0x41465257); }
 af_rw_effect_packet_end = .;
 ASSERT(. <= 0x807D6040, "Golden reward effects exceed their reservation")
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
}
