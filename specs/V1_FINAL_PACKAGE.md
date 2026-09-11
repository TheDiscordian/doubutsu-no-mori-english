# V1 Final package

Package the completed main-program diagnostic build as `V1 Final`. All tracked
V1-01 through V1-29 findings have implementations; the final stage adds thirteen
in-place literals to the complete RC8 content without changing executable code
or saved formats. Do not build another RC, replay the construction chain, or
repeat accepted hardware checks.

Bind the exact final ROM, UPS, completed diagnostic receipt, committed builder,
and recorded correction-baseline receipt. Read the latest development ROM and
metadata only; no old candidate ROM or save is needed. Reject missing/altered
receipts, changed outputs, dirty source, and existing output destinations.

The final ZIP contains exactly ten files: the UPS, manifest, README, SOURCES,
TOOLCHAIN, BUG_REPORT, tooling licence, standalone patcher, binary helper, and
checksums. Local application needs only Python 3 and the supported original
ROM. Include no ROM, save, loose game artwork, or private machine paths.
Verify every relative document link and member checksum.

The final manifest separates final-build, baseline-build, and packaging
revisions. Preserve prior human acceptance of V1-01 through V1-23 and ordinary
save/restart/reload without claiming new execution of later labels. Forward and
backward compatibility with RC8 are expected without migration, not independently
tested. Require Expansion Pak, 128-KiB FlashRAM, and RTC. Preserve older artifacts.

Execute the final ZIP's own standalone patcher once against the original ROM,
requiring the exact complete final cartridge and valid boot checksum before
writing the handoff directory. This final-package check does not require any
emulator, old-build test, or full suite. Focused tests cover new manifest/content,
source bindings, checksums, document links, and rejected receipts.

Neutral tools, room surfaces, effects, and fish/insect textures are not a V1
review task absent actual lettering or a concrete defect. Preserve native/GC
presentation intent and the user's retained lucky-bag decoration. V2 redesign
stays deferred. Broader untested gameplay remains explicit in the final notes.
Packaging is local/private; public upload and repository publication require
separate approval and redistribution review.
