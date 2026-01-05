# Medical De-identification Web Backend

FastAPI backend for the PHI de-identification web interface.

## Features

- File upload and management (Excel, CSV, JSON, TXT)
- PHI detection and masking with configurable settings
- Real-time processing status updates
- Report generation
- Regulation management (HIPAA, Taiwan PDPA)

## Development

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn main:app --reload --port 8000
```

## API Endpoints

- `POST /api/upload` - Upload files
- `GET /api/files` - List uploaded files
- `GET /api/preview/{file_id}` - Preview file content
- `POST /api/process` - Start PHI processing
- `GET /api/tasks` - List processing tasks
- `GET /api/reports` - List generated reports
- `GET /api/settings/phi-types` - Get available PHI types
- `GET /api/regulations` - List loaded regulations
