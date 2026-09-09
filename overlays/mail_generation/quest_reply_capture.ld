OUTPUT_ARCH(mips)
SECTIONS
{
    . = 0x80B00000;
    __capture_start = .;
    .text : { digest.o(.text) . = ALIGN(16); npc_capture.o(.text) . = ALIGN(16); generate.o(.text) . = ALIGN(16); npc_creator.o(.text) . = ALIGN(16); mother_creator.o(.text) . = ALIGN(16); departed_creator.o(.text) . = ALIGN(16); villager_event_creator.o(.text) . = ALIGN(16); academy_creator.o(.text) . = ALIGN(16); academy_score_creator.o(.text) . = ALIGN(16); post_office_creator.o(.text) . = ALIGN(16); museum_creator.o(.text) . = ALIGN(16); shop_notice_creator.o(.text) . = ALIGN(16); quest_reply_creator.o(.text) . = ALIGN(16); sources.o(.text) . = ALIGN(16); }
    _af_npc_captureSegmentTextSize = SIZEOF(.text);
    .data : { *(.data) . = ALIGN(16); }
    _af_npc_captureSegmentDataSize = SIZEOF(.data);
    .rodata : { digest.o(.rodata) . = ALIGN(16); npc_capture.o(.rodata) . = ALIGN(16); generate.o(.rodata) . = ALIGN(16); npc_creator.o(.rodata) . = ALIGN(16); mother_creator.o(.rodata) . = ALIGN(16); departed_creator.o(.rodata) . = ALIGN(16); villager_event_creator.o(.rodata) . = ALIGN(16); academy_creator.o(.rodata) . = ALIGN(16); academy_score_creator.o(.rodata) . = ALIGN(16); post_office_creator.o(.rodata) . = ALIGN(16); museum_creator.o(.rodata) . = ALIGN(16); shop_notice_creator.o(.rodata) . = ALIGN(16); quest_reply_creator.o(.rodata) . = ALIGN(16); academy_score_sources.o(.rodata) . = ALIGN(16); sources.o(.rodata) . = ALIGN(16); }
    _af_npc_captureSegmentRoDataSize = SIZEOF(.rodata);
    .bss (NOLOAD) : { *(.bss .bss.* COMMON) }
    _af_npc_captureSegmentBssSize = SIZEOF(.bss);
    __capture_end = .;
    ASSERT(SIZEOF(.bss) == 0, "Quest reply creator retains mutable state")
    ASSERT(SIZEOF(.data) == 0, "Quest reply creator contains writable data")
    ASSERT(__capture_end - __capture_start <= AF_CREATOR_IMAGE_MAX, "Quest reply creator exceeds bounded allocation")
    .ovl : { relocation.o(.ovl) }
    /DISCARD/ : { *(.comment .note.* .reginfo .MIPS.abiflags .pdr .gnu.attributes) }
}
