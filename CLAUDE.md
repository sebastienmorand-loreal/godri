# Godri - Google Drive CLI Tool

## Project Overview

Godri is a comprehensive Python CLI tool for Google Drive and Google Workspace operations with modern typer-based hierarchical command structure, async architecture, and modular MCP (Model Context Protocol) server integration. It provides complete functionality for Google Drive, Docs, Sheets, Slides, Forms, Translation, and Speech services.

## Architecture

### Core Components

- **CLI Entry Point**: `src/godri/main.py` - Typer-based hierarchical command structure with rich console output
- **CLI Commands**: `src/godri/cli/` - Modular command structure (auth, drive, docs, mcp, translate)
- **API Wrappers**: `src/godri/commons/api/` - Async aiohttp-based Google API clients
- **Utilities**: `src/godri/commons/utils/` - Caching, helpers, range parsing, color conversion
- **MCP Server**: `src/godri/mcpservers/` - Modular FastMCP server with separated tool modules
- **Authentication**: `src/godri/services/auth_service_new.py` - Async OAuth2 flow with persistent token storage

### Service Architecture

```
GodriCLI (main.py) - Typer-based CLI
├── cli/                           # Modular CLI commands
│   ├── auth.py                   # Authentication commands
│   ├── drive.py                  # Drive operations
│   ├── docs.py                   # Document operations
│   ├── mcp.py                    # MCP server commands
│   └── translate.py              # Translation commands
├── commons/                       # Shared utilities and API wrappers
│   ├── api/                      # Async API clients
│   │   ├── google_api_client.py  # Base aiohttp Google API client
│   │   ├── drive_api.py          # Drive API wrapper
│   │   ├── docs_api.py           # Docs API wrapper
│   │   ├── sheets_api.py         # Sheets API wrapper
│   │   ├── slides_api.py         # Slides API wrapper
│   │   ├── forms_api.py          # Forms API wrapper
│   │   ├── translate_api.py      # Translation API wrapper
│   │   └── speech_api.py         # Speech API wrapper
│   └── utils/                    # Utilities and helpers
│       ├── cache.py              # Async TTL caching
│       ├── color_converter.py    # Color conversion utilities
│       ├── file_helpers.py       # File operation helpers
│       └── range_parser.py       # Range parsing logic
├── mcpservers/                    # Modular MCP server
│   ├── main_server.py            # Main MCP server entry point
│   ├── base_tools.py             # Abstract base class for tools
│   ├── drive_tools.py            # Drive MCP tools
│   ├── docs_tools.py             # Docs MCP tools
│   ├── sheets_tools.py           # Sheets MCP tools
│   ├── slides_tools.py           # Slides MCP tools
│   ├── forms_tools.py            # Forms MCP tools
│   ├── translate_tools.py        # Translation MCP tools
│   └── speech_tools.py           # Speech MCP tools
└── services/                      # Legacy/authentication services
    ├── auth_service_new.py       # New async authentication
    └── auth_service.py           # Legacy authentication (deprecated)
```

### Dependency Injection Pattern

The new architecture follows async dependency injection:
- **CLI**: Services instantiated per command with async initialization
- **MCP Server**: Global service instances with lazy loading in `mcpservers/main_server.py`
- **API Clients**: All async with aiohttp, injected into tool modules
- **Caching**: Async cache with TTL support reduces API call redundancy
- **Authentication**: Async OAuth2 service with automatic token refresh

## Key Features Implemented

### Async Architecture
- **aiohttp Integration**: All Google API clients use aiohttp for optimal performance
- **Connection Pooling**: Efficient session management and connection reuse
- **Non-blocking Operations**: Full async/await pattern throughout the codebase
- **Concurrent Processing**: Batch operations with proper concurrency control

### Advanced Caching System
- **TTL-based Caching**: Configurable time-to-live for different API operations
- **Per-key Locking**: Prevents cache stampedes with async locking mechanisms
- **Memory Efficient**: Automatic cleanup of expired cache entries
- **Redundancy Reduction**: Significantly reduces Google API quota usage

### Modular Architecture
- **Separated Concerns**: CLI, API wrappers, utilities, and MCP tools in dedicated modules
- **Abstract Base Classes**: Consistent tool implementation with BaseTools pattern
- **Typer CLI**: Modern CLI framework with rich console output and command hierarchy
- **Tool Modularity**: MCP server split into focused tool modules by service area

### Range Support System
- **Slides**: Range parsing for slide operations (1-3, 1,3,5, 2-4,6-8)
- **Download**: Slide range downloads in multiple formats
- **Copy**: Range-based slide copying between presentations
- **Utility Module**: Centralized range parsing logic in `commons/utils/range_parser.py`

### Copy Functionality
- **Slides Copy**: Copy slides between presentations with theme preservation and source linking
- **Sheets Copy**: Copy sheets between spreadsheets with format preservation and collision handling
- **Batch Operations**: Multiple slide/sheet copying with detailed error reporting
- **Async Processing**: Non-blocking copy operations for better performance

### Content Management
- **Slides Content**: Comprehensive content listing with formatting details, position, size
- **Text Formatting**: Rich text formatting support similar to Google Sheets
- **Element Management**: Add/remove/move content elements on slides
- **Color Utilities**: Advanced color conversion and management in `commons/utils/color_converter.py`

### Translation Integration
- **Document Translation**: Preserves formatting while translating content
- **Sheet Translation**: Range-based translation with formula preservation
- **Smart Detection**: Automatically skips non-translatable content
- **Forms Translation**: Translate questions and options while preserving structure

### Forms Management System
- **Complete CRUD Operations**: Full create, read, update, delete for forms, sections, and questions
- **1-Based Numbering**: User-friendly numbering system (Section 7 = Training, Question 20 = "Are you trained in IP?")
- **Automatic Index Conversion**: All MCP tools and CLI convert 1-based user input to 0-based internal indexing
- **Section Navigation**: Support for section navigation logic and conditional flow
- **Question Types**: Text, choice, scale, date, time, file upload with proper validation
- **Translation Support**: Translate questions and answer options while preserving form structure
- **Positioning Control**: Insert sections and questions at specific positions (before/after/end)

### Speech Processing
- **Audio Transcription**: Google Speech-to-Text API integration with multiple format support
- **Format Detection**: Automatic audio format detection with mutagen library
- **Language Support**: Multi-language transcription with auto-detection capabilities
- **Async Processing**: Non-blocking audio processing for large files

## Development Standards

### Code Formatting
**MANDATORY**: Always run `black -l 120 src/` after ANY code modifications and BEFORE any git operations, builds, or deployments.

### Project Structure
```
godri/
├── src/godri/
│   ├── main.py                   # Typer-based CLI entry point
│   ├── cli/                      # Modular CLI commands
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication commands
│   │   ├── drive.py             # Drive operations
│   │   ├── docs.py              # Docs operations
│   │   ├── mcp.py               # MCP server commands
│   │   └── translate.py         # Translation commands
│   ├── commons/                  # Shared utilities and API wrappers
│   │   ├── __init__.py
│   │   ├── api/                 # Async API clients using aiohttp
│   │   │   ├── __init__.py
│   │   │   ├── google_api_client.py # Base Google API client
│   │   │   ├── drive_api.py     # Drive API wrapper
│   │   │   ├── docs_api.py      # Docs API wrapper
│   │   │   ├── sheets_api.py    # Sheets API wrapper
│   │   │   ├── slides_api.py    # Slides API wrapper
│   │   │   ├── forms_api.py     # Forms API wrapper
│   │   │   ├── translate_api.py # Translate API wrapper
│   │   │   └── speech_api.py    # Speech API wrapper
│   │   ├── utils/               # Utility classes and helpers
│   │   │   ├── __init__.py
│   │   │   ├── cache.py         # Async caching system
│   │   │   ├── color_converter.py # Color conversion utilities
│   │   │   ├── file_helpers.py  # File operation helpers
│   │   │   └── range_parser.py  # Range parsing for slides/sheets
│   │   └── models/              # Data models and schemas
│   │       └── __init__.py
│   ├── mcpservers/              # Modular MCP server components
│   │   ├── __init__.py
│   │   ├── main_server.py       # Main MCP server entry point
│   │   ├── base_tools.py        # Abstract base class for tools
│   │   ├── drive_tools.py       # Drive MCP tools
│   │   ├── docs_tools.py        # Docs MCP tools
│   │   ├── sheets_tools.py      # Sheets MCP tools
│   │   ├── slides_tools.py      # Slides MCP tools
│   │   ├── forms_tools.py       # Forms MCP tools
│   │   ├── translate_tools.py   # Translation MCP tools
│   │   └── speech_tools.py      # Speech MCP tools
│   ├── services/                # Legacy service layer (being migrated)
│   │   ├── __init__.py
│   │   ├── auth_service_new.py  # New async authentication service
│   │   └── auth_service.py      # Legacy authentication (deprecated)
│   ├── config/
│   │   ├── __init__.py
│   │   └── logging_config.py    # Centralized logging configuration
│   └── e2e_tests/               # End-to-end test suite
│       ├── __init__.py
│       ├── test_file_operations.py # File create/read/upload/download tests
│       └── test_integration.py  # Integration tests
├── pyproject.toml               # UV dependency configuration
├── uv.lock                      # UV lock file
├── README.md                    # Comprehensive documentation
└── CLAUDE.md                    # This file
```

### Dependencies Management
- **Package Manager**: UV (`uv run pip install -e .`, `uv add`, `uv sync` for development)
- **Installation**: `uv run pip install -e .` (installs `godri` command globally in development mode)
- **Python Version**: 3.11+
- **Key Dependencies**: 
  - **CLI**: typer, rich (modern CLI with beautiful output)
  - **Async**: aiohttp, aiofiles (async HTTP client and file operations)
  - **Google APIs**: google-api-python-client, google-auth-httplib2, google-auth-oauthlib
  - **Translation**: google-cloud-translate
  - **Speech**: google-cloud-speech, mutagen (audio format detection)
  - **MCP**: mcp, fastapi, uvicorn, starlette (Model Context Protocol server)
  - **Development**: black, bandit, pytest

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

# Run security scan
bandit -r src/

# Run end-to-end tests
uv run src/godri/e2e_tests/test_file_operations.py
```

### Testing New Architecture
```bash
# Test typer CLI structure
godri --help                         # Show available commands
godri auth --help                    # Authentication options
godri drive --help                   # Drive operations
godri docs --help                    # Document operations
godri translate --help               # Translation options
godri mcp --help                     # MCP server options

# Test async operations
godri drive search --name "test" --limit 5
godri docs create-document "Test Doc" --content "Test content"
godri translate "Hello world" "fr"

# Test MCP server modular architecture
godri mcp stdio                      # Start modular MCP server
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

### Async Architecture Implementation
- **GoogleApiClient**: Base aiohttp client with session management and token refresh
- **Connection Pooling**: Efficient HTTP connection reuse across all API calls
- **Async Context Managers**: Proper resource cleanup with async context managers
- **Error Handling**: Comprehensive async error handling with retry logic

### Caching System (`commons/utils/cache.py`)
- **AsyncCache**: TTL-based caching with per-key async locking
- **Memory Management**: Automatic cleanup of expired entries
- **Cache Keys**: Intelligent key generation for different API operations
- **Performance**: Significantly reduces API quota usage and improves response times

### Range Parsing (`commons/utils/range_parser.py`)
- **Centralized Logic**: Unified range parsing for slides and sheets operations
- **Format Support**: "1-3", "1,3,5", "2-4,6-8" formats with validation
- **Error Handling**: Comprehensive validation with user-friendly error messages
- **Async Ready**: Designed for async operations and batch processing

### MCP Server Architecture (`mcpservers/`)
- **Modular Design**: Separated tool modules by service area (drive, docs, sheets, etc.)
- **BaseTools**: Abstract base class ensuring consistent tool implementation
- **FastMCP Integration**: Uses FastMCP framework with proper async handling
- **Service Initialization**: Lazy loading with global service instances and proper cleanup
- **Tool Documentation**: Comprehensive docstrings for all 40+ MCP tools
- **Structured Data**: List[List] support for sheets values operations
- **Complete Formatting**: Full parity with CLI formatting capabilities

### CLI Architecture (`main.py` + `cli/`)
- **Typer Framework**: Modern CLI with rich console output and auto-completion
- **Modular Commands**: Separated command modules for better maintainability
- **Rich Output**: Colored console output with progress indicators
- **Error Handling**: Consistent error handling with user-friendly messages
- **Async Integration**: Proper async command handling with typer

### Color Conversion (`commons/utils/color_converter.py`)
- **Multiple Formats**: Support for hex, RGB, HSL, and Google API color formats
- **Validation**: Comprehensive color format validation
- **Conversion**: Seamless conversion between different color representations
- **Google API**: Proper formatting for Google Sheets and Slides color APIs

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
# After making changes (MANDATORY)
black -l 120 src/           # Format code
bandit -r src/              # Security scan
uv run src/godri/e2e_tests/test_file_operations.py  # Run tests
git add .
git commit -m "[STRYxxxxxxx](type) Descriptive commit message"
```

## Migration Status

### Completed
- ✅ Typer-based CLI architecture
- ✅ Async API clients with aiohttp
- ✅ Advanced caching system with TTL support
- ✅ Modular MCP server architecture
- ✅ Utility modules (cache, color converter, file helpers, range parser)
- ✅ End-to-end test framework
- ✅ New authentication service
- ✅ Project structure reorganization

### In Progress
- 🔄 CLI commands migration: auth, drive, docs, mcp, translate (completed)
- 🔄 CLI commands migration: sheets, slides, forms, speech (pending)
- 🔄 Documentation updates (README.md, CLAUDE.md)

### Next Steps
1. Complete remaining CLI command migrations
2. Enhance end-to-end test coverage
3. Optimize caching strategies for specific operations
4. Add comprehensive error handling and user guidance
5. Performance testing and optimization

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