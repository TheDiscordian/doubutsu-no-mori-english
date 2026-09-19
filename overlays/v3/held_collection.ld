OUTPUT_ARCH(mips)
ENTRY(af_v3_held_catalogue_record)
af_v3_held_item_collection = 0x804A6600;
af_v3_prior_catalogue_record = 0x80466F00;
af_v3_prior_catalogue_owned = 0x80466F10;
af_v3_require_save_state = 0x804692F4;
af_v3_save_halt = 0x80469270;
af_v3_save_collect = 0x8046B9C4;
SECTIONS
{
    . = 0x804AFA00;
    .text : {
        *(.text.af_v3_held_catalogue_record)
        ASSERT(. <= 0x804AFB00, "Held recording exceeds fixed entry slot");
        . = 0x100;
        *(.text.af_v3_held_catalogue_owned)
        *(.text .text.*)
    }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) }
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    ASSERT(. <= 0x804AFFF0, "Held collection overlaps equipment guard")
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Unexpected collection state")
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
