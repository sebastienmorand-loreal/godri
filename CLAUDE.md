# Godri - Google Drive CLI Tool

## Project Overview

Godri is a comprehensive Python CLI tool for Google Drive and Google Workspace operations with hierarchical command structure and MCP (Model Context Protocol) server integration. It provides complete functionality for Google Drive, Docs, Sheets, Slides, Forms, and Translation services.

## Architecture

### Core Components

- **CLI Entry Point**: `src/godri/main.py` - Main application with argparse-based hierarchical command structure
- **Authentication**: `src/godri/services/auth_service.py` - OAuth2 flow with persistent token storage
- **Service Layer**: Individual service classes for each Google API
- **MCP Server**: `src/godri/services/mcp_server.py` - FastMCP integration for AI assistant access

### Service Architecture

```
GodriCLI (main.py)
├── AuthService (auth_service.py) - OAuth2 authentication
├── DriveService (drive_service.py) - File operations, smart download
├── DocsService (docs_service.py) - Document CRUD, markdown support
├── SheetsService (sheets_service.py) - Spreadsheet operations, formatting
├── SlidesService (slides_service.py) - Presentation operations, content management
├── FormsService (forms_service.py) - Forms CRUD operations, 1-based numbering
└── TranslateService (translate_service.py) - Text translation
```

### Dependency Injection Pattern

All services follow the same dependency injection pattern:
- Services instantiated in `main.py:initialize_services()` 
- AuthService passed to all other services in constructor
- All services have async `initialize()` method

## Key Features Implemented

### Range Support System
- **Slides**: Range parsing for slide operations (1-3, 1,3,5, 2-4,6-8)
- **Download**: Slide range downloads in multiple formats
- **Copy**: Range-based slide copying between presentations

### Copy Functionality
- **Slides Copy**: Copy slides between presentations with theme preservation and source linking
- **Sheets Copy**: Copy sheets between spreadsheets with format preservation and collision handling
- **Batch Operations**: Multiple slide/sheet copying with detailed error reporting

### Content Management
- **Slides Content**: Comprehensive content listing with formatting details, position, size
- **Text Formatting**: Rich text formatting support similar to Google Sheets
- **Element Management**: Add/remove/move content elements on slides

### Translation Integration
- **Document Translation**: Preserves formatting while translating content
- **Sheet Translation**: Range-based translation with formula preservation
- **Smart Detection**: Automatically skips non-translatable content

### Forms Management System
- **Complete CRUD Operations**: Full create, read, update, delete for forms, sections, and questions
- **1-Based Numbering**: User-friendly numbering system (Section 7 = Training, Question 20 = "Are you trained in IP?")
- **Automatic Index Conversion**: All MCP tools and CLI convert 1-based user input to 0-based internal indexing
- **Section Navigation**: Support for section navigation logic and conditional flow
- **Question Types**: Text, choice, scale, date, time, file upload with proper validation
- **Translation Support**: Translate questions and answer options while preserving form structure
- **Positioning Control**: Insert sections and questions at specific positions (before/after/end)

## Development Standards

### Code Formatting
**MANDATORY**: Always run `black -l 120 src/` after ANY code modifications and BEFORE any git operations, builds, or deployments.

### Project Structure
```
godri/
├── src/godri/
│   ├── main.py                 # CLI entry point with hierarchical commands
│   ├── config/
│   │   └── logging_config.py   # Logging configuration
│   └── services/
│       ├── auth_service.py     # OAuth2 authentication
│       ├── drive_service.py    # Google Drive operations
│       ├── docs_service.py     # Google Docs with markdown support
│       ├── sheets_service.py   # Google Sheets comprehensive operations
│       ├── slides_service.py   # Google Slides comprehensive operations
│       ├── forms_service.py    # Google Forms comprehensive operations
│       ├── translate_service.py # Translation service
│       └── mcp_server.py       # MCP server implementation
├── pyproject.toml              # UV dependency configuration
├── uv.lock                     # UV lock file
└── README.md                   # Comprehensive documentation
```

### Dependencies Management
- **Package Manager**: UV (`uv run pip install -e .`, `uv add`, `uv sync` for development)
- **Installation**: `uv run pip install -e .` (installs `godri` command globally in development mode)
- **Python Version**: 3.11+
- **Key Dependencies**: google-api-python-client, mcp, fastapi, aiofiles, aiohttp

## Common Commands

### Development
```bash
# Option 1: Install package (development mode) - Recommended
uv run pip install -e .
godri <command>

# Option 2: Run directly from source (for local testing before install)
uv sync
uv run src/godri/main.py <command>

# Format code (MANDATORY before commits)
black -l 120 src/

# Test authentication
godri auth                           # After install
# OR
uv run src/godri/main.py auth        # Direct from source

# Start MCP server
godri mcp stdio                      # After install
# OR
uv run src/godri/main.py mcp stdio   # Direct from source
```

### Testing Copy Features
```bash
# After install (recommended)
godri slides copy SOURCE_ID TARGET_ID "1-3,5"
godri sheets copy SOURCE_ID TARGET_ID "Sheet1" "Sheet2"
godri slides content list PRESENTATION_ID "1-3" --detailed

# OR direct from source (for local testing)
uv run src/godri/main.py slides copy SOURCE_ID TARGET_ID "1-3,5"
uv run src/godri/main.py sheets copy SOURCE_ID TARGET_ID "Sheet1" "Sheet2"
uv run src/godri/main.py slides content list PRESENTATION_ID "1-3" --detailed
```

## Authentication Setup

### Environment Variables
```bash
export GODRI_CLIENT_FILE="/path/to/client_secret.json"
```

### Token Storage
- Location: `~/.godri-token.json`
- Auto-refresh: Handled by AuthService
- MCP Integration: Automatically loads token for MCP server

## Key Implementation Details

### Range Parsing (`slides_service.py`)
- `_parse_slide_range()`: Converts range strings to slide numbers
- `_expand_slide_identifiers()`: Maps user numbers to API object IDs
- Supports: "1-3", "1,3,5", "2-4,6-8" formats

### Copy Implementation
- **Slides**: Uses Google Slides API with theme import/export
- **Sheets**: Uses Google Sheets copyTo API with batch operations
- **Error Handling**: Comprehensive error reporting for batch operations

### MCP Server (`mcp_server.py`)
- **FastMCP Integration**: Uses FastMCP framework
- **Service Initialization**: Lazy loading with global service instances
- **Tool Documentation**: Comprehensive docstrings for all MCP tools
- **Structured Data**: List[List] support for sheets values operations
- **Complete Formatting**: Full parity with CLI formatting capabilities (format_range, copy_format, set_column_width)

### CLI Command Structure (`main.py`)
- **Hierarchical Commands**: drive, docs, sheets, slides, translate, mcp
- **Subcommand Handlers**: Pattern-based handler methods
- **Argument Parsing**: Comprehensive argparse configuration

## File-Specific Guidelines

### `main.py` (2000+ lines)
- **Command Handlers**: All async methods following `handle_*` pattern
- **Service Initialization**: Single `initialize_services()` method
- **Argument Parser**: Comprehensive hierarchical structure in `create_parser()`
- **Error Handling**: Consistent logging and sys.exit(1) pattern

### `slides_service.py`
- **Range Support**: Core range parsing and expansion logic
- **Content Management**: Detailed content extraction with formatting
- **Copy Operations**: Theme preservation and source linking support

### `sheets_service.py`
- **Copy Operations**: Single and multiple sheet copying
- **Collision Handling**: Automatic name resolution for duplicates
- **Format Preservation**: Complete formatting and structure preservation

### `forms_service.py`
- **1-Based Numbering**: All user-facing operations use 1-based section/question numbering
- **API Detection**: Checks for `pageBreakItem` key instead of `itemType` for section detection
- **CRUD Operations**: Complete form, section, and question management
- **Translation Integration**: Question and answer option translation support
- **Section Navigation**: Support for conditional section navigation and flow control

### `mcp_server.py`
- **Tool Definitions**: All tools use @mcp.tool decorator
- **Service Access**: Global service instances with lazy initialization
- **Error Handling**: Comprehensive try/catch with user-friendly messages
- **Forms Tools**: 12 comprehensive tools with 1-based numbering and automatic index conversion
- **Sheets Tools**: 13 comprehensive tools including formatting (format_range, copy_format, set_column_width)
- **Structured Data**: JSON List[List] support for values_read/values_set operations
- **Full CLI Parity**: All CLI formatting capabilities available through MCP tools

## Testing Approach

### Manual Testing
- Create test presentations and spreadsheets for copy operations
- Test range parsing with various formats
- Verify theme preservation and formatting retention
- Test MCP tools through CLI equivalents
- Test Forms 1-based numbering with real forms (sections and questions)
- Verify Forms translation preserves structure and formatting

### Error Scenarios
- Invalid slide/sheet/form references
- Permission errors (especially Forms API access)
- API quota limits
- Network connectivity issues
- Forms section/question numbering confusion (1-based vs 0-based)
- Forms API pageBreakItem vs itemType detection issues

## Common Issues & Solutions

### Authentication Issues
- Run `godri auth --force` to re-authenticate
- Verify `GODRI_CLIENT_FILE` environment variable
- Check Google Cloud API enablement

### Range Parsing Issues
- Use quotes around ranges: `"1-3,5"`
- Verify slide/sheet existence before range operations
- Check user-friendly numbers vs API object IDs

### Copy Operation Issues
- Verify source and target IDs are correct
- Check permissions on target documents
- Monitor API quota usage in Google Cloud Console

### Forms Operation Issues
- Ensure Google Forms API is enabled in Google Cloud Console
- Remember that section/question numbers are 1-based (Section 7 = Training)
- Verify form permissions for write operations
- Check form ID format (different from Drive file IDs)

## Git Workflow

```bash
# After making changes
black -l 120 src/
git add .
git commit -m "Descriptive commit message"
```

## Future Development Guidelines

### Adding New Features
1. Implement service layer method first
2. Add CLI command handler in main.py
3. Add MCP tool in mcp_server.py
4. Update README.md documentation
5. Format code with Black
6. Test thoroughly before committing

### Extending Copy Functionality
- Follow existing pattern in slides_service.py and sheets_service.py
- Implement batch operations with detailed error reporting
- Add range support for applicable operations
- Ensure MCP tool integration

### API Integration
- All Google API calls should be in service layer
- Use consistent error handling patterns
- Implement retry logic for transient failures
- Follow Google API best practices for batching