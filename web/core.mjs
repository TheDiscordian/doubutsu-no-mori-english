/* Browser-only ROM reconstruction. No storage, network, or UI side effects. */
const MAX = 64 * 1024 * 1024;
const DISC_SIZE = 1459978240;
const ascii = new TextDecoder('utf-8', { fatal: true });
function require(value, message) { if (!value) throw new Error(message); }
function integer(n, min, max, what) {
  require(Number.isSafeInteger(n) && n >= min && n <= max, `Invalid ${what}.`);
}
function span(at, size, total, what = 'data range') {
  integer(at, 0, total, what); integer(size, 0, total - at, what);
}
const view = b => new DataView(b.buffer, b.byteOffset, b.byteLength);
const magic = (b, word) => word.split('').every((c, i) => b[i] === c.charCodeAt(0));
export async function sha256(bytes) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
    .map(b => b.toString(16).padStart(2, '0')).join('');
}
async function checkHash(bytes, expected, message) {
  require(await sha256(bytes) === expected, message);
}

export function validateManifest(m) {
  require(m?.format === 1, 'This release manifest is not supported.');
  integer(m.source_size, 64, MAX, 'N64 source size');
  integer(m.output_size, m.source_size, MAX, 'output size');
  require(/^[\w ()·.-]+\.z64$/.test(m.output_name), 'Invalid output filename.');
  require(m.disc_id === 'GAFE01' && m.disc_revision === 0, 'Unsupported GameCube release.');
  require(Array.isArray(m.resources) && m.resources.length > 0 && m.resources.length <= 16,
    'Invalid GameCube resource list.');
  const hashes = [m.source_sha256, m.output_sha256, m.recipe?.sha256, m.recipe?.decoded_sha256];
  const names = new Set();
  for (const r of m.resources) {
    require(typeof r.path === 'string' && /^[A-Za-z0-9_./-]+$/.test(r.path) &&
      !r.path.startsWith('/') && !r.path.split('/').some(p => !p || p === '.' || p === '..') &&
      !names.has(r.path), 'Invalid GameCube resource path.');
    names.add(r.path);
    integer(r.size, 1, MAX, 'resource size'); integer(r.decoded_size, 1, MAX, 'decoded resource size');
    require(['raw', 'yaz0'].includes(r.decode), 'Unsupported donor compression.');
    if (r.decode === 'raw') require(r.size === r.decoded_size, 'Invalid raw resource size.');
    hashes.push(r.sha256, r.decoded_sha256);
  }
  require(hashes.every(h => typeof h === 'string' && /^[0-9a-f]{64}$/.test(h)), 'Invalid release checksum.');
  require(m.recipe.file === 'patch.afwp.gz', 'Invalid patch filename.');
  integer(m.recipe.size, 1, MAX, 'patch size');
  integer(m.recipe.decoded_size, 16, MAX, 'decoded patch size');
  return m;
}

export function rejectArchive(file) {
  require(!/\.(7z|zip|rar|gz|rvz|gcz|wbfs|nkit)$/i.test(file.name || ''),
    'Extract archives first. Convert RVZ/GCZ/NKit to a full ISO with Dolphin. This page accepts ROM and disc-image files, not archives.');
}

export function normaliseN64(raw) {
  require(raw.length >= 64 && raw.length % 4 === 0, 'This is not a supported N64 ROM.');
  const code = view(raw).getUint32(0);
  require([0x80371240, 0x37804012, 0x40123780].includes(code),
    'The N64 file is not a recognised .z64, .v64, or .n64 ROM. Extract it from its archive first.');
  const bytes = raw.slice();
  if (code === 0x37804012) {
    for (let i = 0; i < bytes.length; i += 2) [bytes[i], bytes[i + 1]] = [bytes[i + 1], bytes[i]];
  } else if (code === 0x40123780) {
    for (let i = 0; i < bytes.length; i += 4) {
      [bytes[i], bytes[i + 1], bytes[i + 2], bytes[i + 3]] = [bytes[i + 3], bytes[i + 2], bytes[i + 1], bytes[i]];
    }
  }
  return bytes;
}

export class GameCubeDisc {
  constructor(file) { this.file = file; this.offsets = null; }
  async physical(at, size) {
    span(at, size, this.file.size, 'disc-image range');
    const bytes = new Uint8Array(await this.file.slice(at, at + size).arrayBuffer());
    require(bytes.length === size, 'The GameCube image is truncated.');
    return bytes;
  }
  async open(id = 'GAFE01', revision = 0) {
    rejectArchive(this.file);
    require(this.file.size >= 0x440, 'The GameCube image is too small.');
    const first = await this.physical(0, 8);
    if (magic(first, 'CISO')) {
      const header = await this.physical(0, 0x8000);
      this.blockSize = view(header).getUint32(4, true);
      integer(this.blockSize, 512, 0x1000000, 'CISO block size');
      require((this.blockSize & (this.blockSize - 1)) === 0, 'Invalid CISO block size.');
      this.offsets = new Int32Array(0x8000 - 8).fill(-1);
      let physical = 0x8000;
      for (let i = 0; i < this.offsets.length; i++) {
        require(header[i + 8] <= 1, 'Unsupported CISO block map.');
        if (header[i + 8]) {
          span(physical, this.blockSize, this.file.size, 'CISO block');
          this.offsets[i] = physical; physical += this.blockSize;
        }
      }
    }
    this.header = await this.read(0, 0x440);
    require(view(this.header).getUint32(0x1c) === 0xc2339f3d, 'This is not a GameCube disc image.');
    require(ascii.decode(this.header.subarray(0, 6)) === id && this.header[7] === revision,
      'Use Animal Crossing (USA, Canada), GAFE01 revision 0. This is a different game, region, or revision.');
    return this;
  }
  async read(at, size) {
    span(at, size, DISC_SIZE, 'GameCube disc range');
    integer(size, 0, MAX, 'disc read size');
    if (!this.offsets) return this.physical(at, size);
    const out = new Uint8Array(size);
    for (let done = 0; done < size;) {
      const logical = at + done, block = Math.floor(logical / this.blockSize);
      require(block < this.offsets.length, 'CISO does not cover this disc range.');
      const within = logical % this.blockSize;
      const count = Math.min(this.blockSize - within, size - done);
      if (this.offsets[block] >= 0) out.set(await this.physical(this.offsets[block] + within, count), done);
      done += count;
    }
    return out;
  }
  async files() {
    const hv = view(this.header), start = hv.getUint32(0x424), size = hv.getUint32(0x428);
    integer(size, 12, 8 * 1024 * 1024, 'GameCube file table size');
    const data = await this.read(start, size), v = view(data);
    require(data[0] === 1 && v.getUint32(4) === 0, 'Invalid GameCube root directory.');
    const count = v.getUint32(8);
    integer(count, 1, Math.floor(data.length / 12), 'GameCube file count');
    const strings = count * 12, result = new Map();
    const directories = [{ index: 0, end: count, path: '' }];
    for (let i = 1; i < count; i++) {
      while (directories.at(-1)?.end === i) directories.pop();
      const parent = directories.at(-1);
      require(parent && i < parent.end, 'Invalid GameCube directory boundaries.');
      const word = v.getUint32(i * 12), kind = word >>> 24;
      const nameAt = strings + (word & 0xffffff), end = data.indexOf(0, nameAt);
      require(kind <= 1 && nameAt >= strings && end >= nameAt && end - nameAt <= 255,
        'Invalid GameCube filename.');
      const name = ascii.decode(data.subarray(nameAt, end));
      require(name && name !== '.' && name !== '..' && !/[\x00-\x1f\\/]/.test(name), 'Unsafe GameCube filename.');
      const path = parent.path + name;
      require(!result.has(path), 'Duplicate GameCube filename.');
      const offset = v.getUint32(i * 12 + 4), length = v.getUint32(i * 12 + 8);
      if (kind) {
        require(offset === parent.index && length > i && length <= parent.end, 'Invalid GameCube subdirectory.');
        result.set(path, { directory: true });
        directories.push({ index: i, end: length, path: path + '/' });
      } else {
        span(offset, length, DISC_SIZE, 'GameCube file range');
        result.set(path, { offset, size: length });
      }
    }
    return result;
  }
}

export function decodeYaz0(raw, expected) {
  require(raw.length >= 16 && magic(raw, 'Yaz0'), 'Invalid Yaz0 donor resource.');
  const size = view(raw).getUint32(4);
  integer(size, 1, MAX, 'Yaz0 output size');
  require(size === expected, 'Unexpected Yaz0 output size.');
  const out = new Uint8Array(size);
  let input = 16, output = 0, bits = 0, code = 0;
  const take = () => { require(input < raw.length, 'Truncated Yaz0 resource.'); return raw[input++]; };
  while (output < size) {
    if (!bits) { code = take(); bits = 8; }
    if (code & 128) out[output++] = take();
    else {
      const a = take(), b = take(), distance = ((a & 15) << 8 | b) + 1;
      const length = (a >> 4) ? (a >> 4) + 2 : take() + 18;
      require(distance <= output && length <= size - output, 'Invalid Yaz0 back-reference.');
      for (let j = 0; j < length; j++) { out[output] = out[output - distance]; output++; }
    }
    code <<= 1; bits--;
  }
  return out;
}

export async function decompressRecipe(compressed, expected) {
  integer(expected, 16, MAX, 'decoded patch size');
  const reader = new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip')).getReader();
  const out = new Uint8Array(expected);
  let at = 0;
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      require(value.length <= expected - at, 'Patch exceeds its declared size.');
      out.set(value, at); at += value.length;
    }
    require(at === expected, 'The patch is truncated.');
    return out;
  } catch (error) {
    await reader.cancel().catch(() => {});
    throw new Error('Cannot decode the patch. Reload the page and try again.', { cause: error });
  } finally { reader.releaseLock(); }
}

export function applyRecipe(source, donors, recipe, outputSize) {
  integer(outputSize, source.length, MAX, 'ROM output size');
  require(recipe.length >= 16 && recipe.length <= MAX && magic(recipe, 'AFWP0001'), 'Invalid patch recipe.');
  const v = view(recipe), count = v.getUint32(8, true), literalSize = v.getUint32(12, true);
  integer(count, 1, 1000000, 'patch command count');
  const literalAt = 16 + count * 16;
  require(literalAt + literalSize === recipe.length, 'Invalid patch command table.');
  const pools = [recipe.subarray(literalAt), ...donors];
  const out = new Uint8Array(outputSize); out.set(source);
  let previousEnd = 0, literalCursor = 0;
  for (let i = 0; i < count; i++) {
    const at = 16 + i * 16, destination = v.getUint32(at, true), length = v.getUint32(at + 4, true);
    const sourceIndex = v.getUint32(at + 8, true), offset = v.getUint32(at + 12, true);
    require(length > 0 && destination >= previousEnd && sourceIndex < pools.length, 'Invalid or overlapping patch command.');
    span(destination, length, out.length, 'patch destination');
    span(offset, length, pools[sourceIndex].length, 'patch source');
    if (!sourceIndex) {
      require(offset === literalCursor, 'Invalid patch literal order.'); literalCursor += length;
    }
    out.set(pools[sourceIndex].subarray(offset, offset + length), destination);
    previousEnd = destination + length;
  }
  require(literalCursor === literalSize, 'Unused patch literal data.');
  return out;
}

export async function buildRom(n64, gamecube, manifest, loadRecipe, progress = () => {}) {
  const m = validateManifest(manifest);
  rejectArchive(n64); rejectArchive(gamecube);
  require(n64.size === m.source_size, 'Use the original, unpatched 16 MiB Doubutsu no Mori (Japan) ROM.');
  progress(5, 'Checking your Nintendo 64 ROM…');
  const source = normaliseN64(new Uint8Array(await n64.arrayBuffer()));
  await checkHash(source, m.source_sha256, 'The N64 checksum does not match. Use an unmodified Doubutsu no Mori (Japan) ROM.');
  progress(15, 'Opening your GameCube disc…');
  const disc = await new GameCubeDisc(gamecube).open(m.disc_id, m.disc_revision);
  const entries = await disc.files(), donors = [];
  for (const [i, r] of m.resources.entries()) {
    progress(20 + i * 12, `Reading English donor data (${i + 1}/${m.resources.length})…`);
    const file = entries.get(r.path);
    require(file && !file.directory && file.size === r.size, `Missing or changed GameCube resource: ${r.path}.`);
    const raw = await disc.read(file.offset, file.size);
    await checkHash(raw, r.sha256, `The GameCube donor checksum does not match: ${r.path}. Use an unmodified USA/Canada disc.`);
    const decoded = r.decode === 'yaz0' ? decodeYaz0(raw, r.decoded_size) : raw;
    await checkHash(decoded, r.decoded_sha256, `Decoded GameCube resource failed verification: ${r.path}.`);
    donors.push(decoded);
  }
  progress(60, 'Getting the translation patch…');
  const compressed = await loadRecipe(m.recipe);
  require(compressed.length === m.recipe.size, 'The patch download is incomplete. Reload and try again.');
  await checkHash(compressed, m.recipe.sha256, 'Patch checksum mismatch. Reload the page and try again.');
  progress(70, 'Unpacking the translation…');
  const recipe = await decompressRecipe(compressed, m.recipe.decoded_size);
  await checkHash(recipe, m.recipe.decoded_sha256, 'Decoded patch checksum mismatch.');
  progress(85, 'Putting your English game together…');
  const output = applyRecipe(source, donors, recipe, m.output_size);
  progress(95, 'Verifying the finished ROM…');
  await checkHash(output, m.output_sha256, 'The finished ROM failed verification. No download has been created.');
  progress(100, 'Your English ROM is ready.');
  return { output, receipt: { build: m.build, source_sha256: m.source_sha256,
    output_sha256: m.output_sha256, gamecube_id: m.disc_id,
    donor_sha256: Object.fromEntries(m.resources.map(r => [r.path, r.sha256])),
    patch_sha256: m.recipe.sha256, requirements: m.requirements,
    save_compatibility: m.save_compatibility } };
}
