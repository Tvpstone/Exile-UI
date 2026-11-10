"""Minimal in-place editor for the ini-files that Exile UI (AutoHotkey v1) reads and writes.

AHK's IniWrite keeps the file's existing encoding (UTF-16 LE with BOM on Unicode builds, or
whatever the file was created with), so this editor detects the encoding on load and writes it back
unchanged. Only the targeted key is touched; comments, ordering and other keys stay as they are.
Section and key names are matched case-insensitively, like AHK does.
"""
import os
import tempfile


def _decode(raw: bytes):
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16"), "utf-16", True
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8"), "utf-8", True
    try:
        return raw.decode("utf-8"), "utf-8", False
    except UnicodeDecodeError:
        return raw.decode("cp1252"), "cp1252", False


def _encode(text: str, encoding: str, bom: bool) -> bytes:
    if encoding == "utf-16":
        return b"\xff\xfe" + text.encode("utf-16-le")
    if encoding == "utf-8":
        return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")
    return text.encode(encoding)


class IniFile:
    def __init__(self, path):
        self.path = path
        self.encoding, self.bom = "utf-8", False
        self.newline = "\r\n"
        self.lines = []
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            self.lines = []
            return
        with open(self.path, "rb") as f:
            text, self.encoding, self.bom = _decode(f.read())
        self.newline = "\r\n" if "\r\n" in text else ("\n" if "\n" in text else "\r\n")
        self.lines = text.splitlines()

    # ---- helpers -------------------------------------------------------------------------
    def _section_range(self, section):
        """Return (header_index, end_index) of a section, or None. end is exclusive."""
        header = None
        for i, line in enumerate(self.lines):
            s = line.strip()
            if s.startswith("[") and s.endswith("]"):
                if header is not None:
                    return header, i
                if s[1:-1].strip().lower() == section.lower():
                    header = i
        return (header, len(self.lines)) if header is not None else None

    def _find_key(self, section, key):
        rng = self._section_range(section)
        if rng is None:
            return None, rng
        for i in range(rng[0] + 1, rng[1]):
            line = self.lines[i]
            if line.lstrip().startswith(";") or "=" not in line:
                continue
            if line.split("=", 1)[0].strip().lower() == key.lower():
                return i, rng
        return None, rng

    # ---- public API ----------------------------------------------------------------------
    def get(self, section, key, default=None):
        idx, _ = self._find_key(section, key)
        if idx is None:
            return default
        return self.lines[idx].split("=", 1)[1].strip()

    def set(self, section, key, value):
        value = str(value)
        idx, rng = self._find_key(section, key)
        if idx is not None:
            self.lines[idx] = self.lines[idx].split("=", 1)[0] + "=" + value
        elif rng is not None:
            # insert after the last non-blank line of the section
            pos = rng[1]
            while pos > rng[0] + 1 and not self.lines[pos - 1].strip():
                pos -= 1
            self.lines.insert(pos, f"{key}={value}")
        else:
            if self.lines and self.lines[-1].strip():
                self.lines.append("")
            self.lines += [f"[{section}]", f"{key}={value}"]

    def save(self):
        text = self.newline.join(self.lines) + self.newline
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(_encode(text, self.encoding, self.bom))
            os.replace(tmp, self.path)  # atomic, so AHK never reads a half-written file
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
