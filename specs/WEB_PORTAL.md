# Browser patch portal

## Contract

Create the exact current V2-07 N64 cartridge in a static website using the user's
Japanese N64 ROM and English USA/Canada GameCube disc. Both files stay in the
browser. There is no upload endpoint, telemetry, account, or external asset CDN.
The local service binds to loopback. Public hosting is not authorised.

Supported inputs are extracted `.z64`, `.v64`, and `.n64` cartridges, and
`.iso`, `.gcm`, and sparse GameCube `.ciso` discs. Archives and RVZ are rejected
with an explanation. Normalise cartridge byte order, then require the Japanese
retail SHA-256. Require GameCube ID `GAFE01`, revision 0, and exact hashes for
the donor files actually read. Do not require a whole-disc allocation or pretend
that checking a disc header verifies its contents.

The GameCube input supplies actual matching English/resource spans. A prepared
multi-source recipe copies those spans from hashed disc resources and carries
the remaining changes as compressed literals. This is not an ownership check
or an encrypted patch unlocked by a disc hash. It also does not establish that
all game-derived content is absent from the patch or grant redistribution rights.

## Recipe format

`AFWP0001` (8 ASCII bytes), little-endian u32 command count and literal length,
then commands of four little-endian u32 fields: output offset, length, source
index, and source offset. Source 0 is the trailing literal buffer; sources 1+
are the manifest's ordered GameCube resource buffers, optionally Yaz0-decoded.
The output starts with the original N64 data, zero-extended to the output size.
Commands are sorted and non-overlapping. Every read/write and decompression is
bounded. The transport is gzip with compressed and expanded SHA-256 hashes.

The manifest binds source/output sizes and hashes, cartridge version, donor
paths and raw/decoded hashes, recipe identity, and required hardware. The builder
verifies the recipe recreates the existing cartridge; it does not rebuild the
translation. The browser verifies the complete output before exposing a download.
Generated recipes, media, and site exports remain in ignored `build/` paths.

## Browser and interface

Use the public-facing name **Animal Crossing N64**. Explain the required games,
patching, downloads, privacy, and hardware needs without private candidate names
or local-preview FAQs. Keep the staging/deployment status in operator documents
and release metadata. The input FAQ presents exact, format-labelled MD5 values,
including file sizes for GameCube disc representations and the catalogued source
of the full-disc hash. Manual MD5 comparisons do not replace SHA-256 verification.

Use a module worker for file reads, hashing, decoding, and patch application.
Read GameCube slices through the File API, including CISO's allocation map.
Cancel terminates the worker. Changing inputs invalidates the previous download;
temporary object URLs are revoked. Errors identify the relevant input/stage,
and progress remains visible to assistive technology. No automatic download,
file overwrite, persistent ROM storage, or audio autoplay occurs.

All assets use relative paths so a repository subpath works on static hosting.
The generated site is the entire server root; never serve the repository, source
ROMs, saves, or local research directories. A restrictive CSP and a read-only
local server support the no-upload design. Publication is a separate explicit
action; no active Pages deployment workflow is installed.

## Verification

Run focused synthetic parser/recipe tests and a real headless-browser patch using
the supplied files. Compare the downloaded result to the exact V2-07 hash. Check
bad/wrong inputs, corruption, cancellation, input changes, narrow layouts, relative
paths, and network requests. Inspect desktop/mobile screenshots silently. No
emulator replay or old-cartridge testing is needed for this portal.

## Platform references

- [File slicing in workers](https://developer.mozilla.org/en-US/docs/Web/API/Blob/slice)
- [SHA-256 in a secure browser context](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/digest)
- [Native gzip decompression](https://developer.mozilla.org/en-US/docs/Web/API/DecompressionStream)
- [Module workers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers)
- [Static GitHub Pages sites](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
