"""tri-Ace SLZ codec (modes 0-3), shared by the Star Ocean PSP/PS2 archives.

Container header (16 bytes): b"SLZ" + mode, u32 compressed, u32 unpacked,
u32 next_rel (relative offset of a following member, 0 when single).

The decoder is the ground truth; the mode-2 encoder is the optimal-parse
compressor carried over from the Star Ocean 3 project.
"""
from __future__ import annotations

import struct
from collections import deque

try:
    import numpy as _np
except ImportError:
    _np = None


# ---------------------------------------------------------------------------
# decoder
# ---------------------------------------------------------------------------

def decompress_payload(payload: bytes, mode: int, output_size: int) -> bytes:
    if mode == 0:
        if len(payload) < output_size:
            raise ValueError("short mode-0 SLZ payload")
        return payload[:output_size]
    if mode not in (1, 2, 3):
        raise ValueError(f"unsupported SLZ mode {mode}")
    src = 0
    out = bytearray()
    flags = 0
    while len(out) < output_size:
        flags >>= 1
        if flags <= 0xFFFF:
            if src >= len(payload):
                raise ValueError("SLZ flags truncated")
            flags = 0x00FF0000 | payload[src]
            src += 1
            if mode == 3:
                if src >= len(payload):
                    raise ValueError("SLZ16 flags truncated")
                flags |= 0xFF000000 | (payload[src] << 8)
                src += 1
        if flags & 1:
            unit = 2 if mode == 3 else 1
            if src + unit > len(payload):
                raise ValueError("SLZ literal truncated")
            out.extend(payload[src: src + unit])
            src += unit
        else:
            if src + 2 > len(payload):
                raise ValueError("SLZ match truncated")
            pos, count = payload[src], payload[src + 1]
            src += 2
            if mode == 2 and count >= 0xF0:
                if count > 0xF0:
                    count = (count & 0x0F) + 3
                else:
                    count = pos + 0x13
                    if src >= len(payload):
                        raise ValueError("SLZ RLE truncated")
                    pos = payload[src]
                    src += 1
                out.extend(bytes((pos,)) * min(count, output_size - len(out)))
            else:
                pos |= (count & 0x0F) << 8
                count = (count >> 4) + 3
                if mode == 3:
                    pos <<= 1
                    count = (count - 1) << 1
                if pos == 0 or pos > len(out):
                    raise ValueError(f"invalid SLZ distance {pos} at output {len(out)}")
                for _ in range(min(count, output_size - len(out))):
                    out.append(out[-pos])
    return bytes(out)


def is_slz(blob: bytes) -> bool:
    return len(blob) >= 16 and blob[:3] == b"SLZ" and blob[3] in (0, 1, 2, 3)


def parse_header(blob: bytes, off: int = 0):
    mode = blob[off + 3]
    comp, unp, nxt = struct.unpack_from("<3I", blob, off + 4)
    return mode, comp, unp, nxt


def parse_chain(blob: bytes):
    """Members of an SLZ container: [(mode, comp, unp, next_rel, offset)].

    A container can be a chain (next_rel > 1 points at the following member);
    the decoded output is the concatenation of every member's output, so a
    rebuild has to keep both the per-member modes and the chain links.
    """
    out = []
    off = 0
    while True:
        if blob[off:off + 3] != b"SLZ":
            raise ValueError(f"not SLZ at {off}")
        mode, comp, unp, nxt = parse_header(blob, off)
        out.append((mode, comp, unp, nxt, off))
        if nxt <= 1:
            break
        off += nxt
    return out


def decompress(blob: bytes) -> bytes:
    """Decode one SLZ container (following the next_rel chain if present)."""
    out = bytearray()
    for mode, comp, unp, _nxt, off in parse_chain(blob):
        payload = blob[off + 16: off + 16 + comp]
        out.extend(decompress_payload(payload, mode, unp))
    return bytes(out)


def recompress_like(blob: bytes, data: bytes, limit: int | None = None) -> bytes:
    """Re-encode `data` keeping the container shape of the original `blob`.

    Per-member decoded sizes, per-member modes and the chain links are all
    preserved, because the engine may well have a different decode path per
    data kind - swapping a mode is what broke the first build.  Mode 3 has no
    encoder here and falls back to mode 0 (stored), which the game uses too.
    `limit` is the byte slot the result has to fit into.
    """
    chain = parse_chain(blob)
    total = sum(unp for _m, _c, unp, _n, _o in chain)
    if total != len(data):
        raise ValueError(f"size mismatch: chain wants {total}, got {len(data)}")
    members = []
    pos = 0
    for mode, _comp, unp, _nxt, _off in chain:
        chunk = data[pos:pos + unp]
        pos += unp
        if mode == 0:
            members.append((0, chunk, unp))
        elif mode in (1, 2):
            # the mode is part of the container shape, so a member that no
            # longer compresses is a failure, not a reason to switch to stored
            members.append((mode, compress_payload(chunk, mode), unp))
        else:
            raise ValueError(f"no encoder for SLZ mode {mode}")
    # Keep every header field retail wrote - including `compressed`, which the
    # new payload is padded out to.  The decoder stops at `unpacked`, so the
    # slack is ignored, and in exchange each member, each chain link and the
    # container as a whole stay at exactly the size and offset they had.
    # Shrinking `compressed` moves whatever follows a member and is what the
    # earlier builds got wrong.
    out = bytearray()
    for (o_mode, comp, unp, nxt, _off), (m, payload, _u) in zip(chain, members):
        if len(payload) > comp:
            raise ValueError(f"payload {len(payload)} exceeds retail comp {comp}")
        out += b"SLZ" + bytes((m,)) + struct.pack("<3I", comp, unp, nxt)
        out += payload + b"\x00" * (comp - len(payload))
        if nxt > 1:                       # retail pads the link out to 4
            out += b"\x00" * (nxt - 16 - comp)
    if limit is not None and len(out) > limit:
        raise ValueError(f"recompressed {len(out)} bytes exceeds slot {limit}")
    return bytes(out)


# ---------------------------------------------------------------------------
# mode-2 optimal encoder (see SO3 slz_optimal.py for the full derivation)
# ---------------------------------------------------------------------------

_WINDOW = 0xFFF
_MATCH_MAX = 17


def _run_lengths_py(data, n):
    run = [1] * n
    nxt = 1
    for i in range(n - 2, -1, -1):
        nxt = nxt + 1 if data[i] == data[i + 1] else 1
        run[i] = nxt
    return run


def _run_lengths_np(data, n):
    a = _np.frombuffer(data, dtype=_np.uint8)
    if n == 1:
        return _np.ones(1, dtype=_np.int64)
    ends = _np.flatnonzero(a[1:] != a[:-1])
    ends = _np.append(ends, n - 1)
    idx = _np.arange(n, dtype=_np.int64)
    return ends[_np.searchsorted(ends, idx)] - idx + 1


def _find_matches_np(data, n, run_arr, match_max=_MATCH_MAX):
    a8 = _np.frombuffer(data, dtype=_np.uint8)
    maxlen = _np.zeros(n, dtype=_np.int32)
    mdist = _np.zeros(n, dtype=_np.int32)
    if n < 3:
        return maxlen.tolist(), mdist.tolist()
    interior = _np.empty(n, dtype=bool)
    interior[0] = False
    _np.equal(a8[1:], a8[:-1], out=interior[1:])
    deep = interior & (run_arr >= match_max)
    maxlen[deep] = match_max
    mdist[deep] = 1
    cand = _np.flatnonzero(~deep)
    a = a8.astype(_np.uint64)
    ids = [None] * 9
    ids[1] = a
    c256 = _np.uint64(256)
    for k in range(2, 9):
        ids[k] = ids[k - 1][: n - k + 1] * c256 + a[k - 1:]
    for L in range(3, match_max + 1):
        m = n - L + 1
        cand = cand[cand < m]
        if cand.size < 2:
            break
        if L <= 8:
            k1 = ids[L][cand]
            order = _np.argsort(k1, kind="stable")
            s1 = k1[order]
            same = s1[1:] == s1[:-1]
        elif L <= 16:
            k1 = ids[8][cand]
            k2 = ids[L - 8][cand + 8]
            order = _np.lexsort((k2, k1))
            s1, s2 = k1[order], k2[order]
            same = (s1[1:] == s1[:-1]) & (s2[1:] == s2[:-1])
        else:
            k1 = ids[8][cand]
            k2 = ids[8][cand + 8]
            k3 = ids[L - 16][cand + 16]
            order = _np.lexsort((k3, k2, k1))
            s1, s2, s3 = k1[order], k2[order], k3[order]
            same = (s1[1:] == s1[:-1]) & (s2[1:] == s2[:-1]) & (s3[1:] == s3[:-1])
        p = cand[order]
        d = p[1:] - p[:-1]
        ok = same & (d <= _WINDOW)
        tgt = p[1:][ok]
        maxlen[tgt] = L
        mdist[tgt] = d[ok]
        keep = _np.zeros(p.size, dtype=bool)
        keep[1:] = ok
        keep[:-1] |= ok
        cand = _np.sort(p[keep])
    return maxlen.tolist(), mdist.tolist()


def _find_matches_chains(data, n, run, max_chain, match_max=_MATCH_MAX):
    maxlen = [0] * n
    mdist = [0] * n
    if n < 3:
        return maxlen, mdist
    head = {}
    prev = [0] * n
    hget = head.get
    unlimited = max_chain <= 0
    carry_len = carry_dist = 0
    for i in range(n - 2):
        r = run[i]
        if i and run[i - 1] > r:
            if r >= match_max:
                maxlen[i] = match_max
                mdist[i] = 1
                carry_len, carry_dist = match_max - 1, 1
                continue
            if r >= 3 and r > carry_len:
                carry_len, carry_dist = r, 1
        if carry_len >= 3:
            best, bd = carry_len, carry_dist
        else:
            best, bd = 2, 0
        key = data[i] | (data[i + 1] << 8) | (data[i + 2] << 16)
        j = hget(key, -1)
        prev[i] = j
        head[key] = i
        ml = min(n - i, match_max)
        if j >= 0 and best < ml:
            lim = max(i - _WINDOW, 0)
            chain = max_chain
            while j >= lim:
                if data[j + best] == data[i + best] and data[j:j + best] == data[i:i + best]:
                    l = best + 1
                    while l < ml and data[j + l] == data[i + l]:
                        l += 1
                    best, bd = l, i - j
                    if l >= ml:
                        break
                if not unlimited:
                    chain -= 1
                    if not chain:
                        break
                j = prev[j]
        if best >= 3:
            maxlen[i], mdist[i] = best, bd
            carry_len, carry_dist = best - 1, bd
        else:
            carry_len = 0
    return maxlen, mdist


def compress_payload(data: bytes, mode: int = 2, *, max_chain: int = 128,
                     engine: str = "auto") -> bytes:
    """Optimal-parse encoder for SLZ mode 1 and mode 2.

    Mode 1 is mode 2 without the RLE escape, so a length nibble of 0xF is
    legal there and matches can reach 18 bytes; mode 2 loses those to the
    escape but gains the RLE tokens.
    """
    if mode == 2:
        return compress_payload_mode2(data, max_chain=max_chain, engine=engine)
    if mode != 1:
        raise ValueError(f"no encoder for SLZ mode {mode}")
    data = bytes(data)
    n = len(data)
    if n == 0:
        return b""
    use_np = _np is not None and engine != "chains"
    if use_np:
        run_arr = _run_lengths_np(data, n)
        maxlen, mdist = _find_matches_np(data, n, run_arr, match_max=18)
    else:
        run = _run_lengths_py(data, n)
        maxlen, mdist = _find_matches_chains(data, n, run, max_chain, match_max=18)

    cost = [0] * (n + 1)
    kind = bytearray(n)          # 0 literal, 1 match
    tlen = [1] * n
    for i in range(n - 1, -1, -1):
        best = cost[i + 1] + 9
        k = 0
        L = 1
        m = maxlen[i]
        if m >= 3:
            seg = cost[i + 3:i + m + 1]
            c = min(seg) + 17
            if c < best:
                best = c
                L = seg.index(c - 17) + 3
                k = 1
        cost[i] = best
        kind[i] = k
        tlen[i] = L

    out = bytearray()
    i = 0
    bit = 8
    flag_pos = 0
    while i < n:
        if bit == 8:
            flag_pos = len(out)
            out.append(0)
            bit = 0
        if kind[i] == 0:
            out[flag_pos] |= 1 << bit
            out.append(data[i])
        else:
            d = mdist[i]
            out.append(d & 0xFF)
            out.append(((tlen[i] - 3) << 4) | (d >> 8))
        bit += 1
        i += tlen[i]
    return bytes(out)


def compress_payload_mode2(data: bytes, *, max_chain: int = 128, engine: str = "auto") -> bytes:
    data = bytes(data)
    n = len(data)
    if n == 0:
        return b""
    use_np = _np is not None and engine != "chains"
    if use_np:
        run_arr = _run_lengths_np(data, n)
        maxlen, mdist = _find_matches_np(data, n, run_arr)
        run = run_arr.tolist()
    else:
        run = _run_lengths_py(data, n)
        maxlen, mdist = _find_matches_chains(data, n, run, max_chain)

    cost = [0] * (n + 1)
    kind = bytearray(n)
    tlen = [1] * n
    dq = deque()
    dq_e = -1
    dq_append, dq_pop, dq_popleft = dq.append, dq.pop, dq.popleft
    for i in range(n - 1, -1, -1):
        best = cost[i + 1] + 9
        k = 0
        L = 1
        m = maxlen[i]
        r = run[i]
        rr = (18 if r > 18 else r) if r >= 4 else 0
        hi = m if m >= rr else rr
        if hi:
            lo = 3 if m else 4
            seg = cost[i + lo:i + hi + 1]
            c = min(seg) + 17
            if c < best:
                best = c
                L = seg.index(c - 17) + lo
                k = 1 if L <= m else 2
        if r >= 19:
            e = i + r
            if e != dq_e:
                dq.clear()
                dq_e = e
            j = i + 19
            cj = cost[j]
            while dq and cost[dq[-1]] >= cj:
                dq_pop()
            dq_append(j)
            hi = min(i + 274, e)
            while dq[0] > hi:
                dq_popleft()
            c = cost[dq[0]] + 25
            if c < best:
                best, k, L = c, 3, dq[0] - i
        cost[i] = best
        kind[i] = k
        tlen[i] = L

    out = bytearray()
    i = 0
    bit = 8
    flag_pos = 0
    while i < n:
        if bit == 8:
            flag_pos = len(out)
            out.append(0)
            bit = 0
        k = kind[i]
        L = tlen[i]
        if k == 0:
            out[flag_pos] |= 1 << bit
            out.append(data[i])
        elif k == 1:
            d = mdist[i]
            out.append(d & 0xFF)
            out.append(((L - 3) << 4) | (d >> 8))
        elif k == 2:
            out.append(data[i])
            out.append(0xF0 | (L - 3))
        else:
            out.append(L - 0x13)
            out.append(0xF0)
            out.append(data[i])
        bit += 1
        i += L
    return bytes(out)


def compress(data: bytes, mode: int = 2, *, engine: str = "auto") -> bytes:
    """Build a complete single-member SLZ container."""
    if mode == 0:
        payload = bytes(data)
    elif mode == 2:
        payload = compress_payload_mode2(data, engine=engine)
    else:
        raise ValueError(f"encoder for SLZ mode {mode} not implemented")
    return b"SLZ" + bytes((mode,)) + struct.pack("<3I", len(payload), len(data), 0) + payload
