OUTPUT_ARCH(mips)
ENTRY(af_design_valid)
SECTIONS {
    . = AF_CARRIED_DESIGN_RAM;
    .text : { KEEP(*(.text.entry)) *(.text .text.*) }
    . = ALIGN(16);
    .rodata : { *(.rodata .rodata.*) }
    /DISCARD/ : { *(.MIPS.abiflags) *(.reginfo) *(.pdr) *(.mdebug*) *(.comment) *(.eh_frame*) }
    ASSERT(. <= AF_CARRIED_DESIGN_RAM + 0x2000, "Design services exceed their prepared reservation")
}
