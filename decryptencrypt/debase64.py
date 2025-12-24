import base64
import binascii
import json
import re
import heapq
from log.log import Log

bs64 = Log("base64")

JV_DROP_INDEXES = {
    "2_1254": (
        (0, 1, 2, 4, 5, 36, 47, 48, 59, 96, 107),
        (0, 2, 3, 4, 5, 36, 47, 48, 59, 96, 107),
    ),
    "2_10234": (
        (0, 1, 2, 4, 5, 6, 7, 46, 65, 66, 198, 270, 328, 329),
        (0, 1, 3, 4, 5, 6, 7, 46, 65, 66, 198, 270, 328, 329),
        (0, 1, 2, 4, 6, 7, 8, 46, 65, 66, 198, 270, 328, 329),
    ),
    "2_9214": (0, 1, 2, 4, 5, 6, 7, 48, 49, 66, 149, 150, 284, 374, 375),
}


def debase64(data: dict or str, required_keys=None):
    """
    Base64 decode helper for API payloads.
    """
    jv_hint = None
    if isinstance(data, dict):
        jv_hint = data.get("jv")
        if "data" not in data:
            return data
        data = data["data"]

    if not isinstance(data, str):
        return data

    if not jv_hint:
        m = re.search(r"jv:([0-9_]+),", data)
        if m:
            jv_hint = m.group(1)

    bs64.logger.info(f"decode start (len={len(data)})")

    def _try_json(text: str):
        if not text:
            return None
        preferred_keys = ("word_list", "topic_code", "task_id", "records")
        required = set(required_keys) if required_keys else None
        best = None
        # Some payloads decode without the leading "{". Try adding it back.
        if text.startswith("\"") and text.rstrip().endswith("}"):
            candidate = "{" + text
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    if required:
                        if any(k in parsed for k in required):
                            return parsed
                    if any(k in parsed for k in preferred_keys):
                        return parsed
                    best = parsed
            except Exception:
                pass
        # Try parsing the whole JSON first when it looks complete.
        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}")
            if end > start:
                full = text[start:end + 1]
                try:
                    parsed = json.loads(full)
                    if isinstance(parsed, dict):
                        if required:
                            if any(k in parsed for k in required):
                                return parsed
                        if any(k in parsed for k in preferred_keys):
                            return parsed
                        best = parsed
                except Exception:
                    pass
        # Try non-greedy matches to avoid swallowing extra braces.
        for match in re.finditer(r"\{.*?\}", text, flags=re.S):
            chunk = match.group(0)
            try:
                parsed = json.loads(chunk)
            except Exception:
                continue
            if not isinstance(parsed, dict):
                continue
            if required:
                if any(k in parsed for k in required):
                    return parsed
                continue
            if any(k in parsed for k in preferred_keys):
                return parsed
            if best is None:
                best = parsed
        return best

    def _decode_candidate(candidate: str):
        if not candidate:
            return None
        pad = (-len(candidate)) % 4
        if pad:
            candidate += "=" * pad
        try:
            raw = base64.b64decode(candidate.encode("utf-8"), validate=False)
        except Exception:
            return None
        text = raw.decode("utf-8", errors="ignore")
        return _try_json(text)

    def _prefix_score(prefix: bytes):
        if not prefix:
            return -10
        ascii_ok = 0
        non_ascii = 0
        for b in prefix:
            if b in (9, 10, 13) or 32 <= b <= 126:
                ascii_ok += 1
            else:
                non_ascii += 1
        score = ascii_ok - non_ascii * 2
        if prefix.startswith(b"{"):
            score += 50
        if prefix.startswith(b"\""):
            score += 20
        if b'"' in prefix:
            score += 5
        if b":" in prefix:
            score += 5
        return score

    def _prefix_plausible(prefix: bytes):
        if not prefix:
            return True
        if prefix[0] not in (ord("{"), ord("\"")):
            return False
        non_ascii = 0
        for b in prefix[:200]:
            if b in (9, 10, 13) or 32 <= b <= 126:
                continue
            non_ascii += 1
            if non_ascii > 10:
                return False
        return True

    def _strip_jv_prefix(text: str):
        m = re.search(r"jv:[0-9_]+,", text)
        if not m:
            return text
        return text[m.end():]

    def _drop_indices(text: str, indexes):
        drop = set(indexes)
        return "".join(ch for i, ch in enumerate(text) if i not in drop)

    def _iter_drop_indexes(drop):
        if not drop:
            return []
        first = drop[0]
        if isinstance(first, int):
            return [drop]
        return drop

    def _try_jv_deobfuscate(text: str, jv_value: str):
        if not jv_value:
            return None
        drop_sets = JV_DROP_INDEXES.get(jv_value)
        if not drop_sets:
            return None
        cleaned = _strip_jv_prefix(text)
        cleaned = cleaned.replace("-", "+").replace("_", "/")
        for drop in _iter_drop_indexes(drop_sets):
            candidate = _drop_indices(cleaned, drop)
            parsed = _decode_candidate(candidate)
            if parsed is not None:
                return parsed
        return None

    def _beam_deobfuscate(text: str, max_noise: int = 25, window: int = 600, beam: int = 60, required=None):
        text = _strip_jv_prefix(text)
        if not text:
            return None
        if len(text) > window:
            head, tail = text[:window], text[window:]
        else:
            head, tail = text, ""
        required_set = set(required) if required else None

        def _norm_char(ch: str):
            if ch == "-":
                return "+"
            if ch == "_":
                return "/"
            return ch

        candidates = [(0, "", "", b"", b"")]
        for ch in head:
            ch = _norm_char(ch)
            next_candidates = []
            for removed, kept, buf, prefix, tail_bytes in candidates:
                # Skip current char (noise).
                if removed < max_noise:
                    next_candidates.append((removed + 1, kept, buf, prefix, tail_bytes))

                # Keep current char.
                new_buf = buf + ch
                new_kept = kept + ch
                new_prefix = prefix
                new_tail = tail_bytes
                if len(new_buf) == 4:
                    try:
                        raw = base64.b64decode(new_buf.encode("utf-8"), validate=True)
                    except Exception:
                        continue
                    new_buf = ""
                    if len(new_prefix) < 200:
                        new_prefix = new_prefix + raw
                        if len(new_prefix) > 200:
                            new_prefix = new_prefix[:200]
                    if required_set:
                        # Track a small rolling tail for required key detection.
                        new_tail = (new_tail + raw)[-200:]
                        if any(k.encode("utf-8") in new_tail for k in required_set):
                            # Boost prefix score when required key appears.
                            new_prefix = new_prefix + b"{}"
                    if not _prefix_plausible(new_prefix):
                        continue
                next_candidates.append((removed, new_kept, new_buf, new_prefix, new_tail))

            # Keep only the most promising candidates.
            next_candidates.sort(key=lambda c: (c[0], -_prefix_score(c[3])))
            candidates = next_candidates[:beam]

        # Try decoding full candidates.
        for removed, kept, buf, _prefix, _tail in sorted(candidates, key=lambda c: c[0]):
            candidate = kept + tail
            parsed = _decode_candidate(candidate)
            if parsed is not None:
                bs64.logger.info(f"decode ok (beam noise={removed})")
                return parsed
        return None

    allowed_std = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    allowed_url = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=/")

    # Candidate 1: strict base64 charset only.
    cleaned = "".join(ch for ch in data if ch in allowed_std)
    parsed = _decode_candidate(cleaned)
    if parsed is not None:
        bs64.logger.info("decode ok")
        return parsed

    # Candidate 2: urlsafe base64.
    urlsafe_raw = "".join(ch for ch in data if ch in allowed_url)
    urlsafe = urlsafe_raw.replace("-", "+").replace("_", "/")
    parsed = _decode_candidate(urlsafe)
    if parsed is not None:
        bs64.logger.info("decode ok")
        return parsed

    # Candidate 3: longest base64-like segment without regex.
    segment = ""
    current = []
    for ch in data:
        if ch in allowed_url:
            current.append(ch)
        else:
            if len(current) > len(segment):
                segment = "".join(current)
            current = []
    if len(current) > len(segment):
        segment = "".join(current)
    if len(segment) >= 100:
        segment = segment.replace("-", "+").replace("_", "/")
        parsed = _decode_candidate(segment)
        if parsed is not None:
            bs64.logger.info("decode ok")
            return parsed

    parsed = _try_jv_deobfuscate(data, jv_hint)
    if parsed is not None:
        bs64.logger.info("decode ok (jv drop)")
        return parsed

    # Candidate 4: remove every n-th char (noise insertion) on urlsafe data.
    def _try_drop_every_n(src: str, step_min: int = 2, step_max: int = 8):
        for step in range(step_min, step_max + 1):
            for offset in range(step):
                candidate = "".join(ch for i, ch in enumerate(src) if i % step != offset)
                parsed = _decode_candidate(candidate.replace("-", "+").replace("_", "/"))
                if parsed is not None:
                    bs64.logger.info(f"decode ok (drop every {step}th, offset {offset})")
                    return parsed
        return None

    parsed = _try_drop_every_n(urlsafe_raw)
    if parsed is not None:
        return parsed

    # Candidate 5: beam search to drop a small amount of noise in the prefix.
    parsed = _beam_deobfuscate(data, required=required_keys)
    if parsed is not None:
        return parsed

    bs64.logger.error("decode failed")
    raise ValueError("decode failed")


if __name__ == '__main__':
    debase64(
        "EZeJ2uxyJ3b3JkIjoiZG9taW5hdGUiLCJ0b3BpY19jb2RlIoLjoibEZoNWRveHNtTEmlUVmx5SGVIdUxiSmV2WkplU2FsbGlXcHFvbzU3VHhhcVpnNDlxYVdPYmJXdGlqR3FWWmIyK1lHR1JabUp4NvYjI1cmEzR2FhV2hzYjI1cllwREFscE9SalpSbGFXZVRaVzlzWjJsd2NadU5abHlXYUc5dmNIQnNZbWlPYW1obmEydHRiR2Fha0dsbWs1eHZiV3FPYVpNPSIsIm92ZXJfc3RhtdHVzIjoxLCJhbnN3ZXJfcmVzdWx0IjoxLCJjbGVhbl9zdGF0dXMiOjIsImFuc3dlcl9jb3JyZWN0cyI6WzJdfQ=="
    )
