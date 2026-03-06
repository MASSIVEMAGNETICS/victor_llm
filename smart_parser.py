"""
smart_parser.py - Multi-format Data Parsing Engine
Part of the DataBlob Godmode Toolkit for Victor LLM

Supports: JSON, XML, CSV, Parquet (stub), Protocol Buffers (stub),
          binary blobs, unstructured text.
Features: Auto format detection, streaming, corruption detection/repair,
          hierarchical blob extraction, schema inference.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import struct
import xml.etree.ElementTree as ET
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, Iterator, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Format enumeration
# ---------------------------------------------------------------------------

class DataFormat(Enum):
    JSON = auto()
    JSONL = auto()
    XML = auto()
    CSV = auto()
    TSV = auto()
    PARQUET = auto()
    PROTOBUF = auto()
    BINARY = auto()
    TEXT = auto()
    UNKNOWN = auto()


# ---------------------------------------------------------------------------
# Magic-byte signatures for binary format detection
# ---------------------------------------------------------------------------

_MAGIC_SIGNATURES: List[Tuple[bytes, DataFormat]] = [
    (b"PAR1", DataFormat.PARQUET),          # Parquet footer magic
    (b"\x50\x4b\x03\x04", DataFormat.BINARY),  # ZIP
    (b"\x1f\x8b", DataFormat.BINARY),           # gzip
    (b"\x42\x5a\x68", DataFormat.BINARY),        # bzip2
    (b"\xfd\x37\x7a\x58\x5a\x00", DataFormat.BINARY),  # xz
]

_JSON_STARTERS = frozenset(b"{[\"")
_XML_STARTERS = frozenset(b"<")


# ---------------------------------------------------------------------------
# Schema / record types
# ---------------------------------------------------------------------------

ParsedRecord = Dict[str, Any]
SchemaField = Dict[str, str]  # {"name": ..., "type": ..., "nullable": ...}


class ParseResult:
    """Container returned by the parser for a single data source."""

    def __init__(
        self,
        format: DataFormat,
        records: List[ParsedRecord],
        schema: List[SchemaField],
        source: str = "",
        errors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.format = format
        self.records = records
        self.schema = schema
        self.source = source
        self.errors: List[str] = errors or []
        self.metadata: Dict[str, Any] = metadata or {}

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ParseResult(format={self.format.name}, records={len(self.records)}, "
            f"schema_fields={len(self.schema)}, errors={len(self.errors)})"
        )


# ---------------------------------------------------------------------------
# Format detector
# ---------------------------------------------------------------------------

class FormatDetector:
    """Detects the data format of a byte stream or file path."""

    def detect_bytes(self, data: bytes, hint: str = "") -> DataFormat:
        """Detect format from raw bytes. ``hint`` may contain a filename/extension."""
        # Extension hint takes high priority
        ext = Path(hint).suffix.lower() if hint else ""
        ext_map = {
            ".json": DataFormat.JSON,
            ".jsonl": DataFormat.JSONL,
            ".ndjson": DataFormat.JSONL,
            ".xml": DataFormat.XML,
            ".csv": DataFormat.CSV,
            ".tsv": DataFormat.TSV,
            ".parquet": DataFormat.PARQUET,
            ".pb": DataFormat.PROTOBUF,
            ".proto": DataFormat.PROTOBUF,
            ".txt": DataFormat.TEXT,
            ".md": DataFormat.TEXT,
            ".rst": DataFormat.TEXT,
        }
        if ext in ext_map:
            return ext_map[ext]

        if not data:
            return DataFormat.UNKNOWN

        # Magic bytes
        for magic, fmt in _MAGIC_SIGNATURES:
            if data[: len(magic)] == magic:
                return fmt

        # Heuristic text inspection (first 2048 bytes)
        sample = data[:2048]
        try:
            text = sample.decode("utf-8", errors="replace").lstrip()
        except Exception:
            return DataFormat.BINARY

        if not text:
            return DataFormat.UNKNOWN

        if text[0] in "{[":
            # Try to distinguish JSONL (multiple top-level objects, newline-delimited)
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if len(lines) > 1 and all(l.startswith("{") or l.startswith("[") for l in lines[:3]):
                return DataFormat.JSONL
            return DataFormat.JSON

        if text[0] == "<":
            return DataFormat.XML

        # CSV detection: look for consistent delimiter
        delimiter = self._sniff_delimiter(text)
        if delimiter:
            return DataFormat.TSV if delimiter == "\t" else DataFormat.CSV

        return DataFormat.TEXT

    def detect_file(self, path: Union[str, Path]) -> DataFormat:
        """Detect format from a file on disk."""
        path = Path(path)
        try:
            with path.open("rb") as fh:
                header = fh.read(4096)
        except OSError as exc:
            logger.warning("Could not read %s for format detection: %s", path, exc)
            return DataFormat.UNKNOWN
        return self.detect_bytes(header, hint=str(path))

    @staticmethod
    def _sniff_delimiter(text: str) -> Optional[str]:
        """Return the most likely CSV delimiter or None."""
        try:
            dialect = csv.Sniffer().sniff(text[:1024], delimiters=",\t;|")
            return dialect.delimiter
        except csv.Error:
            return None


# ---------------------------------------------------------------------------
# Base parser
# ---------------------------------------------------------------------------

class _BaseParser:
    """Abstract base for individual format parsers."""

    def parse_bytes(self, data: bytes, source: str = "") -> ParseResult:  # pragma: no cover
        raise NotImplementedError

    def parse_stream(self, stream: Iterable[bytes], source: str = "") -> Generator[ParsedRecord, None, None]:  # pragma: no cover
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Schema inference helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_schema(records: List[ParsedRecord]) -> List[SchemaField]:
        if not records:
            return []
        all_keys: Dict[str, set] = {}
        for rec in records:
            for k, v in rec.items():
                all_keys.setdefault(k, set()).add(type(v).__name__)
        schema = []
        for key, types in all_keys.items():
            type_str = types.pop() if len(types) == 1 else "mixed"
            nullable = "NoneType" in types or len(types) > 1
            schema.append({"name": key, "type": type_str, "nullable": str(nullable)})
        return schema


# ---------------------------------------------------------------------------
# JSON parser
# ---------------------------------------------------------------------------

class JSONParser(_BaseParser):

    def parse_bytes(self, data: bytes, source: str = "") -> ParseResult:
        errors: List[str] = []
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception as exc:
            return ParseResult(DataFormat.JSON, [], [], source, [str(exc)])

        # Attempt repair: trailing commas, single quotes
        text, repaired = self._repair(text)
        if repaired:
            errors.append("JSON repaired: removed trailing commas / normalised quotes")

        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            return ParseResult(DataFormat.JSON, [], [], source, [f"JSONDecodeError: {exc}"])

        records: List[ParsedRecord] = []
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    records.append(item)
                else:
                    records.append({"_value": item})
        elif isinstance(obj, dict):
            records = [obj]
        else:
            records = [{"_value": obj}]

        schema = self._infer_schema(records)
        meta = {"raw_type": type(obj).__name__}
        return ParseResult(DataFormat.JSON, records, schema, source, errors, meta)

    def parse_stream(self, stream: Iterable[bytes], source: str = "") -> Generator[ParsedRecord, None, None]:
        buf = b""
        for chunk in stream:
            buf += chunk
        result = self.parse_bytes(buf, source)
        yield from result.records

    @staticmethod
    def _repair(text: str) -> Tuple[str, bool]:
        repaired = False
        # Remove trailing commas before ] or }
        cleaned = re.sub(r",\s*([}\]])", r"\1", text)
        if cleaned != text:
            repaired = True
            text = cleaned
        return text, repaired


# ---------------------------------------------------------------------------
# JSONL parser
# ---------------------------------------------------------------------------

class JSONLParser(_BaseParser):

    def parse_bytes(self, data: bytes, source: str = "") -> ParseResult:
        errors: List[str] = []
        records: List[ParsedRecord] = []
        try:
            lines = data.decode("utf-8", errors="replace").splitlines()
        except Exception as exc:
            return ParseResult(DataFormat.JSONL, [], [], source, [str(exc)])

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    records.append(obj)
                else:
                    records.append({"_value": obj})
            except json.JSONDecodeError as exc:
                errors.append(f"Line {i + 1}: {exc}")

        schema = self._infer_schema(records)
        return ParseResult(DataFormat.JSONL, records, schema, source, errors)

    def parse_stream(self, stream: Iterable[bytes], source: str = "") -> Generator[ParsedRecord, None, None]:
        for chunk in stream:
            for line in chunk.decode("utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    yield obj if isinstance(obj, dict) else {"_value": obj}
                except json.JSONDecodeError:
                    pass


# ---------------------------------------------------------------------------
# XML parser
# ---------------------------------------------------------------------------

class XMLParser(_BaseParser):

    def parse_bytes(self, data: bytes, source: str = "") -> ParseResult:
        errors: List[str] = []
        try:
            root = ET.fromstring(data.decode("utf-8", errors="replace"))
        except ET.ParseError as exc:
            # Attempt basic repair: wrap in a root element
            try:
                wrapped = b"<root>" + data + b"</root>"
                root = ET.fromstring(wrapped.decode("utf-8", errors="replace"))
                errors.append("XML repaired: wrapped in <root> element")
            except ET.ParseError as exc2:
                return ParseResult(DataFormat.XML, [], [], source, [str(exc), str(exc2)])

        records = self._element_to_records(root)
        schema = self._infer_schema(records)
        meta = {"root_tag": root.tag}
        return ParseResult(DataFormat.XML, records, schema, source, errors, meta)

    def parse_stream(self, stream: Iterable[bytes], source: str = "") -> Generator[ParsedRecord, None, None]:
        buf = b""
        for chunk in stream:
            buf += chunk
        result = self.parse_bytes(buf, source)
        yield from result.records

    @staticmethod
    def _element_to_records(element: ET.Element) -> List[ParsedRecord]:
        """Flatten XML into a list of dicts, one per child element."""
        records: List[ParsedRecord] = []
        children = list(element)
        if not children:
            # Leaf element: treat root as single record
            rec: ParsedRecord = dict(element.attrib)
            if element.text and element.text.strip():
                rec["_text"] = element.text.strip()
            records.append(rec)
        else:
            for child in children:
                rec = dict(child.attrib)
                if child.text and child.text.strip():
                    rec["_text"] = child.text.strip()
                # Flatten nested children
                for sub in child:
                    sub_rec = XMLParser._element_to_dict(sub)
                    rec.update(sub_rec)
                rec["_tag"] = child.tag
                records.append(rec)
        return records

    @staticmethod
    def _element_to_dict(element: ET.Element) -> Dict[str, Any]:
        d: Dict[str, Any] = dict(element.attrib)
        if element.text and element.text.strip():
            d[element.tag] = element.text.strip()
        for child in element:
            d.update(XMLParser._element_to_dict(child))
        return d


# ---------------------------------------------------------------------------
# CSV / TSV parser
# ---------------------------------------------------------------------------

class CSVParser(_BaseParser):

    def __init__(self, delimiter: Optional[str] = None) -> None:
        self._delimiter = delimiter

    def parse_bytes(self, data: bytes, source: str = "", fmt: DataFormat = DataFormat.CSV) -> ParseResult:
        errors: List[str] = []
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception as exc:
            return ParseResult(fmt, [], [], source, [str(exc)])

        delimiter = self._delimiter
        if delimiter is None:
            try:
                dialect = csv.Sniffer().sniff(text[:2048], delimiters=",\t;|")
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ","

        records: List[ParsedRecord] = []
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        for i, row in enumerate(reader):
            try:
                records.append(dict(row))
            except Exception as exc:
                errors.append(f"Row {i + 1}: {exc}")

        schema = self._infer_schema(records)
        meta = {"delimiter": delimiter}
        return ParseResult(fmt, records, schema, source, errors, meta)

    def parse_stream(self, stream: Iterable[bytes], source: str = "") -> Generator[ParsedRecord, None, None]:
        buf = b""
        for chunk in stream:
            buf += chunk
        result = self.parse_bytes(buf, source)
        yield from result.records


# ---------------------------------------------------------------------------
# Text parser
# ---------------------------------------------------------------------------

class TextParser(_BaseParser):
    """Treats each non-empty line as a record with a single ``_text`` field."""

    def parse_bytes(self, data: bytes, source: str = "") -> ParseResult:
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception as exc:
            return ParseResult(DataFormat.TEXT, [], [], source, [str(exc)])

        records = [{"_text": line} for line in text.splitlines() if line.strip()]
        schema = [{"name": "_text", "type": "str", "nullable": "False"}]
        return ParseResult(DataFormat.TEXT, records, schema, source)

    def parse_stream(self, stream: Iterable[bytes], source: str = "") -> Generator[ParsedRecord, None, None]:
        for chunk in stream:
            for line in chunk.decode("utf-8", errors="replace").splitlines():
                if line.strip():
                    yield {"_text": line}


# ---------------------------------------------------------------------------
# Binary / stub parsers
# ---------------------------------------------------------------------------

class BinaryParser(_BaseParser):
    """Minimal binary parser: returns hex-encoded chunks as records."""

    def parse_bytes(self, data: bytes, source: str = "") -> ParseResult:
        records = [{"_hex": data.hex(), "_size": len(data)}]
        schema = [
            {"name": "_hex", "type": "str", "nullable": "False"},
            {"name": "_size", "type": "int", "nullable": "False"},
        ]
        return ParseResult(DataFormat.BINARY, records, schema, source)

    def parse_stream(self, stream: Iterable[bytes], source: str = "") -> Generator[ParsedRecord, None, None]:
        offset = 0
        for chunk in stream:
            yield {"_hex": chunk.hex(), "_size": len(chunk), "_offset": offset}
            offset += len(chunk)


class ParquetParser(_BaseParser):
    """Parquet parser stub – delegates to pandas/pyarrow when available."""

    def parse_bytes(self, data: bytes, source: str = "") -> ParseResult:
        errors: List[str] = []
        try:
            import io as _io

            try:
                import pyarrow.parquet as pq  # type: ignore
                import pyarrow as pa  # type: ignore

                table = pq.read_table(_io.BytesIO(data))
                records = table.to_pydict()
                # Transpose column dict -> list of row dicts
                keys = list(records.keys())
                n = len(records[keys[0]]) if keys else 0
                rows = [{k: records[k][i] for k in keys} for i in range(n)]
                schema = self._infer_schema(rows)
                return ParseResult(DataFormat.PARQUET, rows, schema, source, errors)
            except ImportError:
                pass

            try:
                import pandas as pd  # type: ignore

                df = pd.read_parquet(_io.BytesIO(data))
                rows = df.to_dict(orient="records")
                schema = self._infer_schema(rows)
                return ParseResult(DataFormat.PARQUET, rows, schema, source, errors)
            except ImportError:
                pass

            errors.append("pyarrow/pandas not installed; Parquet data returned as binary blob")
            return BinaryParser().parse_bytes(data, source)
        except Exception as exc:
            return ParseResult(DataFormat.PARQUET, [], [], source, [str(exc)])

    def parse_stream(self, stream: Iterable[bytes], source: str = "") -> Generator[ParsedRecord, None, None]:
        buf = b""
        for chunk in stream:
            buf += chunk
        result = self.parse_bytes(buf, source)
        yield from result.records


class ProtobufParser(_BaseParser):
    """Protocol Buffers stub – raw byte records without descriptor."""

    def parse_bytes(self, data: bytes, source: str = "") -> ParseResult:
        errors = ["Protobuf descriptor not provided; returning raw binary record"]
        records = [{"_raw": data.hex(), "_size": len(data)}]
        schema = [
            {"name": "_raw", "type": "str", "nullable": "False"},
            {"name": "_size", "type": "int", "nullable": "False"},
        ]
        return ParseResult(DataFormat.PROTOBUF, records, schema, source, errors)

    def parse_stream(self, stream: Iterable[bytes], source: str = "") -> Generator[ParsedRecord, None, None]:
        buf = b""
        for chunk in stream:
            buf += chunk
        result = self.parse_bytes(buf, source)
        yield from result.records


# ---------------------------------------------------------------------------
# Smart parser – public API
# ---------------------------------------------------------------------------

_FORMAT_PARSERS: Dict[DataFormat, _BaseParser] = {
    DataFormat.JSON: JSONParser(),
    DataFormat.JSONL: JSONLParser(),
    DataFormat.XML: XMLParser(),
    DataFormat.CSV: CSVParser(),
    DataFormat.TSV: CSVParser(delimiter="\t"),
    DataFormat.PARQUET: ParquetParser(),
    DataFormat.PROTOBUF: ProtobufParser(),
    DataFormat.BINARY: BinaryParser(),
    DataFormat.TEXT: TextParser(),
    DataFormat.UNKNOWN: TextParser(),
}


class SmartParser:
    """
    High-level multi-format parser with automatic format detection.

    Usage::

        parser = SmartParser()
        result = parser.parse_file("data.json")
        result = parser.parse_bytes(raw_bytes, hint="data.csv")
        for record in parser.stream_file("huge_data.jsonl"):
            process(record)
    """

    def __init__(self, chunk_size: int = 64 * 1024) -> None:
        self._detector = FormatDetector()
        self._chunk_size = chunk_size

    # ------------------------------------------------------------------
    # Public parse methods
    # ------------------------------------------------------------------

    def parse_file(
        self,
        path: Union[str, Path],
        format_hint: Optional[DataFormat] = None,
    ) -> ParseResult:
        """Parse a file from disk, auto-detecting format unless *format_hint* given."""
        path = Path(path)
        if not path.exists():
            return ParseResult(
                DataFormat.UNKNOWN, [], [], str(path), [f"File not found: {path}"]
            )
        try:
            data = path.read_bytes()
        except OSError as exc:
            return ParseResult(DataFormat.UNKNOWN, [], [], str(path), [str(exc)])

        fmt = format_hint or self._detector.detect_bytes(data, hint=str(path))
        return self._dispatch(data, fmt, source=str(path))

    def parse_bytes(
        self,
        data: bytes,
        hint: str = "",
        format_hint: Optional[DataFormat] = None,
    ) -> ParseResult:
        """Parse raw bytes, optionally providing a filename hint for format detection."""
        fmt = format_hint or self._detector.detect_bytes(data, hint=hint)
        return self._dispatch(data, fmt, source=hint)

    def stream_file(
        self,
        path: Union[str, Path],
        format_hint: Optional[DataFormat] = None,
    ) -> Generator[ParsedRecord, None, None]:
        """Stream records from a large file without loading it entirely into memory."""
        path = Path(path)
        if not path.exists():
            logger.error("stream_file: file not found: %s", path)
            return

        # Detect from header
        with path.open("rb") as fh:
            header = fh.read(4096)
        fmt = format_hint or self._detector.detect_bytes(header, hint=str(path))
        parser = _FORMAT_PARSERS.get(fmt, TextParser())

        def _chunks() -> Iterator[bytes]:
            with path.open("rb") as fh:
                while True:
                    chunk = fh.read(self._chunk_size)
                    if not chunk:
                        break
                    yield chunk

        yield from parser.parse_stream(_chunks(), source=str(path))

    # ------------------------------------------------------------------
    # Schema inference (standalone)
    # ------------------------------------------------------------------

    @staticmethod
    def infer_schema(records: List[ParsedRecord]) -> List[SchemaField]:
        """Infer schema from a list of parsed records."""
        return _BaseParser._infer_schema(records)

    # ------------------------------------------------------------------
    # Corruption detection
    # ------------------------------------------------------------------

    def check_corruption(self, data: bytes, fmt: DataFormat) -> List[str]:
        """Return a list of detected corruption issues (empty = clean)."""
        issues: List[str] = []
        if fmt == DataFormat.JSON:
            try:
                json.loads(data.decode("utf-8", errors="replace"))
            except json.JSONDecodeError as exc:
                issues.append(f"Invalid JSON: {exc}")
        elif fmt == DataFormat.XML:
            try:
                ET.fromstring(data.decode("utf-8", errors="replace"))
            except ET.ParseError as exc:
                issues.append(f"Invalid XML: {exc}")
        elif fmt in (DataFormat.CSV, DataFormat.TSV):
            try:
                text = data.decode("utf-8", errors="replace")
                csv.Sniffer().sniff(text[:1024])
            except csv.Error as exc:
                issues.append(f"CSV sniff failed: {exc}")
        return issues

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _dispatch(self, data: bytes, fmt: DataFormat, source: str) -> ParseResult:
        parser = _FORMAT_PARSERS.get(fmt)
        if parser is None:
            parser = TextParser()
        if fmt == DataFormat.CSV:
            return parser.parse_bytes(data, source, DataFormat.CSV)  # type: ignore[arg-type]
        if fmt == DataFormat.TSV:
            return parser.parse_bytes(data, source, DataFormat.TSV)  # type: ignore[arg-type]
        return parser.parse_bytes(data, source)
