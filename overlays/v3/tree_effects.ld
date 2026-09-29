OUTPUT_ARCH(mips)
ENTRY(af_tree_ready)
SECTIONS {
 . = 0x80780000;
 .text : { *(.text.af_tree_ready) *(.text .text.*) . = ALIGN(16); }
 .rodata : {
   *(.rodata .rodata.*) *(.data .data.*)
   /* Actor pointers and the current seasonal palette directory reset with
      the checked startup packet; no state is left outside that packet. */
   *(.bss .bss.* COMMON) BYTE(0) . = ALIGN(16);
 }
 /DISCARD/ : { *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }
 ASSERT(. <= 0x80788000,"Tree effects exceed the checked code reservation")
}
