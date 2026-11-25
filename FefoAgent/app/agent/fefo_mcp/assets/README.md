# Bundled fonts

`DejaVuSans.ttf` and `DejaVuSans-Bold.ttf` are used by `fefo_mcp/report.py` to render
Turkish characters (ş ğ ı İ ç ö ü) and the lira sign (₺) in PDF reports. The AgentCore
runtime (ARM64 Linux) has no system fonts, so the fonts ship with the CodeZip package.

License: DejaVu fonts / Bitstream Vera license (free to use, embed and redistribute);
see `LICENSE-DejaVu.txt`.
