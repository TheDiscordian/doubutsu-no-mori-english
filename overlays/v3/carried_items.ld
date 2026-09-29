OUTPUT_ARCH(mips)
ENTRY(af_carried_name)
SECTIONS {
 . = DEFINED(AF_CARRIED_LINK_RAM) ? AF_CARRIED_LINK_RAM : 0x80771000;
 af_carried_code_start = .;
 .text : { *(.text.af_carried_name) *(.text .text.*) . = ALIGN(16); }
 .rodata : { *(.rodata .rodata.*) . = ALIGN(16); }
 .forbidden : { *(.data .data.* .bss .bss.* COMMON) }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(SIZEOF(.forbidden) == 0, "Carried items use resident table state")
 ASSERT(. <= af_carried_code_start+0x2800, "Carried code exceeds its reservation")
}
