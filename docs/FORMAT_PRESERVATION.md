# Format Preservation and Asset-Aware Integration

## Current Production Contract

The web workflow must not rebuild user downloads from the PHI audit list.
Processing now creates a de-identified artifact while the raw upload still exists,
then the raw upload may be purged.

Download behavior:

- `file_type=result` returns the generated de-identified source artifact.
- `file_type=report` returns the PHI audit/report export.
- If an old result has no artifact metadata, the backend falls back to the legacy
  JSON/table export path.

## Format Strategy

| Format | Current writer | Fidelity |
| --- | --- | --- |
| CSV | Dialect-aware cell/text patch | Preserves delimiter and row shape |
| XLSX | `openpyxl` patch on a copied workbook | Preserves sheets, styles, widths, formulas not rewritten |
| XLS | Converts to XLSX fallback | Data preserved; legacy workbook styling may not be preserved |
| TXT/MD/JSON/XML/HTML | Text span patch | Text structure preserved, not semantic JSON/XML path patch yet |
| DOCX | Optional `asset-aware-mcp` DFM adapter if installed | Experimental wrapper, disabled unless dependency is present |

## Optional Asset-Aware Runtime

The codebase has a lazy adapter for `asset-aware-mcp`, but the package is not
declared as a project extra yet. In this environment, its transitive cloud
dependency currently fails uv resolution, so adding it to `pyproject.toml` would
break normal backend test and deploy commands.

If a host needs experimental DOCX/DFM or OCR/PDF asset workflows, install
asset-aware into that runtime explicitly after the normal service install:

```bash
uv pip install 'asset-aware-mcp>=0.6.29,<0.7.0'
```

The integration imports asset-aware lazily and keeps all direct imports inside
`core.infrastructure.format_preservation`. This avoids coupling the production
request path to MCP presentation/server code.

If dependency resolution fails, keep DOCX/DFM disabled and use CSV/XLSX
format-preserving exports. The production service targets Python 3.12 today.

## Recommended Upstream API Shape

`asset-aware-mcp` is already useful, but production embedding would be easier if
it exposed a stable library namespace in addition to the MCP tools. Ideal API:

```python
from asset_aware_mcp.dfm import DocxAdapter, DfmIntegrityChecker
from asset_aware_mcp.ocr import OCRProcessor
```

Helpful guarantees for this project:

- Keep DFM/OCR imports free of FastMCP server side effects.
- Split the package into lightweight extras, for example
  `asset-aware-mcp[dfm]`, `asset-aware-mcp[ocr]`, `asset-aware-mcp[pdf-heavy]`,
  so DFM does not force LightRAG/Mistral/Marker dependencies.
- Expose `docx_to_ir(path, work_dir)` and `ir_to_docx(ir, work_dir, output_path)`.
- Expose a text-span replacement helper that preserves run metadata.
- Return structured integrity results, not only markdown strings.
- Keep OCR preprocessing as a small wrapper around `ocrmypdf`, with clear
  language aliases (`zh-tw -> chi_tra`) and no Marker/Torch import unless needed.

Until that API exists, the integration stays behind a thin adapter and imports
the current top-level `src.*` modules lazily.
