# Isolated base translation rebuild

`tools/rebuild_v0.py` constructs the base translation in a new source checkout
whose `build/` starts empty. Its only local data inputs are the verified native
ROM, supplied legacy reference patch, and English GC disc. The legacy patch is
used to corroborate reference identities, not as the translation's output base.
Source/reference checkouts must be clean and pinned; copies of the inputs are
read-only. Existing inputs, development builds, playtest packages, and saves are
not modified. No assets, ROMs, or generated outputs are committed or published.

The recipe regenerates native inventories, GC text/names/glyphs, frozen letter
catalogues, item/name/catchphrase resources, and dialogue candidates. It compiles
the resident module and required overlay variants in the pinned Docker image,
then invokes the existing full integration and finishing installers. All existing
resource, control-code, allocation, relocation, and source-identity checks stay
enabled. Final ROM, patch, and approved report profile must match corrected v0.
The [compiler compatibility contract](PORTABLE_TOOLCHAIN.md) permits only the
two verified image identities; record the actual report hash separately.

Commands and output hashes are recorded at each successful boundary. `--through`
selects a bounded portion of the recipe; `--resume` continues only with unchanged
sources, input identities, commands, and completed output hashes. A failed stage
retains its log and incomplete output rather than overwriting diagnostic evidence.
An interrupted or failed stage is not a successful resumable boundary. Inherited
`AF_` environment overrides cannot redirect this build into another directory.
Only the verified public/legacy compiler selection is explicitly carried into
child commands; resumption requires the same image selection.

This recipe does not rerun emulator scenarios, claim ordinary gameplay or hardware
acceptance, publish a release, or resolve redistribution terms. It uses the
pinned published compiler by default and never distributes the legacy local
development image. Executed results and any missing dependencies
belong in the rebuild checkpoint; a written command list is not proof of a clean
rebuild.
