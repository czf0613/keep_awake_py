"""Keep type stubs parseable by each interpreter in the CI matrix."""

from pathlib import Path


def test_type_stubs_compile():
    source = Path(__file__).resolve().parents[1] / "src" / "keep_awake"
    for stub in source.glob("*.pyi"):
        compile(stub.read_text(encoding="utf-8"), str(stub), "exec")
