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
enabled. Final ROM, patch, and canonical report must match the corrected v0.

Commands and output hashes are recorded at each successful boundary. `--through`
selects a bounded portion of the recipe; `--resume` continues only with unchanged
sources, input identities, commands, and completed output hashes. A failed stage
retains its log and incomplete output rather than overwriting diagnostic evidence.
An interrupted or failed stage is not a successful resumable boundary. Inherited
`AF_` environment overrides cannot redirect this build into another directory.

This recipe does not rerun emulator scenarios, claim ordinary gameplay or hardware
acceptance, publish a release, resolve redistribution terms, or make the local
Docker image available publicly. Executed results and any missing dependencies
belong in the rebuild checkpoint; a written command list is not proof of a clean
rebuild.
