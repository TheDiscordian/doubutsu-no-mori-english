# Scoped release provenance and archive review

This review clarifies actual input use, attribution, and the private package
boundary. It changes documentation only. No ROM, translation payload, source
approval schema, build guard, saved data, or package artifact changes. It is not
legal clearance or a completed public-release approval.

## Source trace

Inspected project revision: `9af27f4c52c1823fa84010f124ef6d815c8ecdce`.
The native and GC reference checkouts match their recorded pins:
`4ddba04604ee7b4c4cfc0b64f8ee4d094bb385be` and
`09ca8e8b5b24e6ab44047ee980cf0088ad7ecb4c`.

- `rebuild_v0` starts from the verified native ROM. `inspect_inputs` applies the
  supplied legacy UPS to a separate inspection copy; inventory/matching consumes
  that copy. It is not the base used by the current cartridge builders.
- `reference_candidates`, `name_candidates`, `display_names`, and
  `item_candidates` take accepted English payloads from bound GC references or
  original translation approvals. Legacy text appears in identity checks, not
  as an automatic substitute for the named English donor.
- `npc_mail_words.prepare` transcodes actual GC entries, checks complete legacy
  agreement, and then applies the separately identified native-species correction.
  `shared_npc_words` preserves those source distinctions.
- `mail_reference.load_reference` binds the supplied GC executable semantics,
  decoder, and all eight mail banks before catalogue construction. The inspected
  mail catalogue does not take its payload from the old translation ROM.
- The native item approval records use `native_name`, source hash, translation,
  and evidence fields. Their loader supplies the source identity; generated
  edits require full provenance. No metadata is added merely to satisfy a generic
  scan, and no provenance guard is weakened.

This trace establishes the inspected paths, not authorship of every byte in
the finished patch or permission to publish it. It does not remove the legacy
reference from the reproducible recipe or relicense any third-party content.

## Notices inspected

| Local source | SHA-256 |
| --- | --- |
| N64 reference `LICENSE` | `a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499` |
| N64 reference `README.md` | `17dc67592f3c8a8a75a72e80435da643e3e8992f93e421a12a3d4ed4d7b5da8e` |
| GC reference `LICENSE` | `36ffd9dc085d529a7e60e1276d73ae5a030b020313e6c5408593a6ae2af39673` |
| Legacy `BEFORE YOU EVEN THINK OF PATCHING!.txt` | `4e71c6867d74815ededf3556457a54a7a192276737530c86cb7cf009ca740d2f` |

The N64 README explicitly excludes `tools/asm-differ`, `tools/asm-processor`,
`tools/fado`, `lib/ultralib`, and `tools/z64compress` from its root licensing
statement. SDK headers and compiler dependencies retain their own notices.
The legacy notes identify Zoinkity and separately credit byuu, _Demo_, Shevious,
and Obsidian for bundled utilities. The invitation to improve the script is not
recorded as a general licence. Those archives and executables remain local.

## Existing package inspection

Inspected archive: `build/v1rc4-package-docs-01/V1RC4-patch.zip`.
SHA-256: `d68abe3651edbc43a73956960a7cbf726edc1967dac8d0085d1868c78c6cf324`.

Read-only checks pass for the exact eight-member archive list, absence of
duplicate members, all seven listed member checksums, and complete equality of
the two patcher files and tooling licence with their current source files.
Members are:

```text
LICENSE-tooling.txt
README.md
SHA256SUMS
SOURCES.md
aflib.py
animal-forest-english.ups
apply_translation.py
manifest.json
```

The manifest retains `public_release: false`, `original_hardware_verified: false`,
and unverified ordinary save/restart. Cartridge source revision remains
`b772f334db544227736d92827f0ed7347f0cce43`; packaging source remains
`4352c37a1105b30fbb934aaf3e6f11b2c1389591`. The already passing standalone
patch application and rebuild are not repeated or presented as new execution.
The new source-note clarifications are not retroactively inside that ZIP.

`gh repo view` confirms `TheDiscordian/doubutsu-no-mori-english` is private.
The tracked root tree contains code, Markdown, JSON, scripts, and the pinned
N64 gitlink, with no tracked ROM, disc, save, image, archive, or executable
asset files identified by extension. This is only a scoped filename inventory:
text and code can still contain third-party-derived content. No public upload,
visibility change, or source release is performed.

The current [release-preparation checklist](../RELEASE_PREPARATION.md) records
remaining redistribution review, public documentation access, release approval,
and gameplay/hardware limits. These facts narrow the outstanding decisions;
they do not declare those decisions complete.
