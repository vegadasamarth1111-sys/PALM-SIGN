"""Export every slide of the deck to PNG for visual review."""

from __future__ import annotations

import sys
from pathlib import Path

import win32com.client as win32

ROOT = Path(__file__).resolve().parent.parent.parent
PPTX = ROOT / "PALM_SIGN_Presentation.pptx"
OUT = Path(__file__).resolve().parent / "_slides"


def main() -> int:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    app = win32.DispatchEx("PowerPoint.Application")
    try:
        pres = app.Presentations.Open(str(PPTX), ReadOnly=True, WithWindow=False)
        for i, slide in enumerate(pres.Slides, 1):
            slide.Export(str(OUT / f"s{i:02d}.png"), "PNG", 1500, 844)
        pres.Close()
        print("exported", len(list(OUT.glob("*.png"))), "slides")
        return 0
    finally:
        app.Quit()


if __name__ == "__main__":
    sys.exit(main())
