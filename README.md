# Godri - Google Drive CLI Tool

A comprehensive Python CLI tool for interacting with Google Drive and Google Workspace APIs (Docs, Sheets, Slides) with translation capabilities.

## Features

- **Authentication**: Console-based OAuth2 authentication using client secret file
- **File Operations**: Search, upload, download files
- **Folder Management**: Create and delete folders
- **Google Docs**: Create and modify Google Documents
- **Google Sheets**: Create and modify Google Spreadsheets
- **Google Slides**: Create and modify Google Presentations
- **Translation**: Translate text using Google Translate API

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
uv sync
```

## Setup

### 1. Google API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Drive API
   - Google Docs API
   - Google Sheets API
   - Google Slides API
   - Google Cloud Translation API
4. Create credentials (OAuth 2.0 Client ID) for a desktop application
5. Download the client secret JSON file

### 2. Environment Variable

Set the `GODRI_CLIENT_FILE` environment variable to point to your client secret file:

```bash
export GODRI_CLIENT_FILE="/path/to/your/client_secret.json"
```

## Usage

### Authentication

First, authenticate with Google APIs:

```bash
uv run src/godri/main.py auth
```

This will open a browser window for OAuth consent and create a `token.json` file for subsequent requests.

### File Operations

#### Search Files

```bash
# Search by query
uv run src/godri/main.py search --query "name contains 'test'"

# Search by name
uv run src/godri/main.py search --name "document"

# Search with MIME type filter
uv run src/godri/main.py search --name "spreadsheet" --mime-type "application/vnd.google-apps.spreadsheet"
```

#### Upload Files

```bash
# Upload to root
uv run src/godri/main.py upload /path/to/file.txt

# Upload to specific folder
uv run src/godri/main.py upload /path/to/file.txt --folder-id "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

# Upload with custom name
uv run src/godri/main.py upload /path/to/file.txt --name "My Custom File"
```

#### Download Files

```bash
uv run src/godri/main.py download "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms" /path/to/output.txt
```

### Folder Management

#### Create Folder

```bash
# Create in root
uv run src/godri/main.py create-folder "My New Folder"

# Create in specific parent folder
uv run src/godri/main.py create-folder "Subfolder" --parent-id "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
```

#### Delete Files/Folders

```bash
uv run src/godri/main.py delete "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
```

### Google Workspace Documents

#### Create Google Doc

```bash
# Create empty document
uv run src/godri/main.py create-doc "My Document"

# Create in specific folder
uv run src/godri/main.py create-doc "My Document" --folder-id "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

# Create with initial content
uv run src/godri/main.py create-doc "My Document" --content "Hello, World!"
```

#### Create Google Sheet

```bash
# Create empty spreadsheet
uv run src/godri/main.py create-sheet "My Spreadsheet"

# Create in specific folder
uv run src/godri/main.py create-sheet "My Spreadsheet" --folder-id "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
```

#### Create Google Slides

```bash
# Create empty presentation
uv run src/godri/main.py create-slides "My Presentation"

# Create in specific folder
uv run src/godri/main.py create-slides "My Presentation" --folder-id "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
```

### Translation

```bash
# Translate text (auto-detect source language)
uv run src/godri/main.py translate "Hello, world!" "fr"

# Translate with specified source language
uv run src/godri/main.py translate "Hello, world!" "fr" --source-language "en"
```

## Command Reference

### Global Options

- `--verbose, -v`: Enable verbose logging

### Commands

- `auth`: Authenticate with Google APIs
- `search`: Search for files
  - `--query, -q`: Search query
  - `--name, -n`: Search by file name
  - `--mime-type, -t`: Filter by MIME type
  - `--limit, -l`: Maximum results (default: 20)
- `upload`: Upload a file
  - `file_path`: Path to file to upload
  - `--folder-id, -f`: Parent folder ID
  - `--name, -n`: Custom file name
- `download`: Download a file
  - `file_id`: File ID to download
  - `output_path`: Output file path
- `create-folder`: Create a folder
  - `name`: Folder name
  - `--parent-id, -p`: Parent folder ID
- `delete`: Delete a file or folder
  - `file_id`: File/folder ID to delete
- `create-doc`: Create a Google Doc
  - `title`: Document title
  - `--folder-id, -f`: Folder ID
  - `--content, -c`: Initial content
- `create-sheet`: Create a Google Sheet
  - `title`: Spreadsheet title
  - `--folder-id, -f`: Folder ID
- `create-slides`: Create a Google Slides presentation
  - `title`: Presentation title
  - `--folder-id, -f`: Folder ID
- `translate`: Translate text
  - `text`: Text to translate
  - `target_language`: Target language code (e.g., 'fr', 'es')
  - `--source-language, -s`: Source language code

## Development

### Project Structure

```
godri/
├── src/godri/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── logging_config.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py   # Authentication
│   │   ├── drive_service.py  # Google Drive operations
│   │   ├── docs_service.py   # Google Docs operations
│   │   ├── sheets_service.py # Google Sheets operations
│   │   ├── slides_service.py # Google Slides operations
│   │   └── translate_service.py # Translation
│   └── models/
│       └── __init__.py
├── pyproject.toml
├── README.md
└── .gitignore
```

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black -l 120 src/
```

## Common MIME Types

- Google Doc: `application/vnd.google-apps.document`
- Google Sheet: `application/vnd.google-apps.spreadsheet`
- Google Slides: `application/vnd.google-apps.presentation`
- Google Folder: `application/vnd.google-apps.folder`
- PDF: `application/pdf`
- Text: `text/plain`
- Image: `image/jpeg`, `image/png`

## Error Handling

The tool includes comprehensive error handling and logging. Use the `--verbose` flag for detailed debugging information.

## Security Notes

- The `token.json` file contains your authentication tokens - keep it secure
- The client secret file should also be kept secure and not committed to version control
- Both files are excluded in the `.gitignore`

## License

This project is for personal/educational use. Please ensure compliance with Google API Terms of Service.