# Leaflet-date, fortune, and glyph-import fixtures

Six selected checks pass, closing four historical fixture errors. No production
code, translation, font pixels, playable ROM, or saved data changes. This is
host-side installation evidence, not newly executed gameplay or hardware proof.

## Changes and retained safeguards

- Fortune catalogue installation and the 128-phrase fortune-string builder use
  the current, source-verified `build/notice-seasonal-runtime` module. Complete
  contents, scoped caller/relocation changes, resource identity, capacity limits,
  and rejection without partial mutation remain checked.
- Leaflet-date tests compose the date-only stage in memory from the verified
  original, current module, numeric dialogue-date installation, and existing
  source-validated hour resource. The tested installer must reconstruct that
  complete expected ROM. Actor relocations, scratch lifetimes, separate numeric
  hour caller, and dependency/source mutation rejection remain checked. This
  isolated installation stage does not replace the final accented event actor.
- The glyph-import builder selects the same current module while retaining the
  independently verified five-glyph font resource. Six full GC references require
  the real font capability even without edit metadata. Missing/damaged resources,
  changed configuration words, and a changed resource blob remain rejected.

The legacy native fortune probe keeps its matched historical fixture. It is not
part of this batch. No source guard is disabled to accept an obsolete module.

## Evidence

The existing full-suite log records errors in the two fortune installation
methods, leaflet installation method, and glyph-import builder method. The
focused commands are:

```sh
PYTHONPATH=tools:tests python3 -m unittest \
  test_leaflet_dates.LeafletDateInstallationTests \
  test_fortune_slips.FortuneSlipSourceTests.test_two_catalog_installation_is_explicit_guarded_and_transactional \
  test_fortune_strings.FortuneTests.test_real_builder_relocates_bank_and_installs_scoped_caller -v

PYTHONPATH=tools:tests python3 -m unittest \
  test_extended_glyph_import.RetailGlyphImportTests.test_builder_requires_verified_resource_even_if_edit_metadata_is_omitted -v
```

Results: five tests pass in 10.322 seconds; the glyph-import test passes in
3.789 seconds. Neither command skips tests. The glyph check is repeated once
because the earlier result is unavailable and its process handle is confirmed
missing; only the recovered execution is counted. The five completed checks
are not repeated. Unselected hour, catalogue-generator, and glyph tests are not
claimed as new passes, and the full suite remains unresolved.

Current module image SHA-256:
`493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6`.
Current module manifest SHA-256:
`c5de2784fc1cbb12bd773c33713648e09f3716968ce3fbab1ddea34b48143f21`.
Leaflet-hour image SHA-256:
`eeb382edeeda4fb8ab3f7c070118a40ae224ee647b5a36b17294c924bec3bfaf`.
Leaflet-hour manifest SHA-256:
`d85b051dc59b58350f75c294cb8c438151e69cebdd0eccc02a16d5887e3bae23`.

Counter-only expectation maintenance remains deferred. Ordinary save/restart,
remaining artwork review, and concrete playtest defects retain their separate
acceptance status; these fixture repairs do not complete those requirements.
