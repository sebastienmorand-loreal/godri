# Godri - Google Drive CLI Tool

A comprehensive Python CLI tool for Google Drive and Google Workspace operations with a clean, hierarchical command structure.

## Features

- **Google Drive**: Search, upload, download files and manage folders
- **Google Docs**: Create, read, and update documents with markdown support
- **Google Sheets**: Comprehensive spreadsheet operations (create, manage sheets, read/write values, formulas, formatting, rows/columns)
- **Google Slides**: Comprehensive presentation operations (create, themes, layouts, slides, content management)
- **Google Forms**: Complete form management (read/write forms, sections, questions, translation with 1-based numbering)
- **Translation**: Translate text using Google Translate API
- **MCP Server**: Model Context Protocol integration with 25+ tools including complete Forms support
- **Authentication**: Secure OAuth2 flow with persistent tokens

## Installation

1. Clone this repository
2. Install the package:

```bash
git clone https://github.com/sebastienmorand-loreal/godri.git
cd godri
uv run pip install -e .
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
   - **Google Forms API** (required for form management)
   - **Google Cloud Translation API** (required for translation features)
4. Create credentials (OAuth 2.0 Client ID) for a desktop application
5. Download the client secret JSON file

### 2. Environment Configuration

Set the `GODRI_CLIENT_FILE` environment variable:

```bash
export GODRI_CLIENT_FILE="/path/to/your/client_secret.json"
```

### 3. Authentication

Authenticate with Google APIs:

```bash
godri auth
```

This opens a browser for OAuth consent and creates `~/.godri-token.json` for subsequent requests.

## Command Structure

Godri uses a clean, hierarchical command structure:

```
godri [--verbose] <command> <subcommand> [args...]
```

## Commands Reference

### Authentication

```bash
# Authenticate with Google APIs
godri auth

# Force re-authentication (delete existing token)
godri auth --force
```

### Google Drive Operations

#### Search Files
```bash
# Search by query
godri drive search --query "name contains 'report'"

# Search by name
godri drive search --name "document" --limit 50

# Search with MIME type filter
godri drive search --name "spreadsheet" --mime-type "application/vnd.google-apps.spreadsheet"
```

#### File Operations
```bash
# Upload file
godri drive upload /path/to/file.txt --folder-id "FOLDER_ID" --name "Custom Name"

# Download file (original format)
godri drive download "FILE_ID" /path/to/output.txt

# Smart download (converts Google Workspace files to Office formats)
godri drive download "FILE_ID" /path/to/output --smart
```

**Smart Download Conversions:**
- Google Docs → Word (.docx)
- Google Sheets → Excel (.xlsx)
- Google Slides → PowerPoint (.pptx)
- Other Google Workspace → PDF (.pdf)

#### Folder Management
```bash
# Create folder
godri drive folder create "My Folder" --parent-id "PARENT_FOLDER_ID"

# Delete file or folder
godri drive folder delete "FILE_OR_FOLDER_ID"
```

### Google Docs Operations

```bash
# Create document
godri docs create-document "Document Title" --folder-id "FOLDER_ID" --content "Initial content" --markdown

# Read document
godri docs read "DOCUMENT_ID" --plain-text

# Update document
godri docs update "DOCUMENT_ID" "New content" --markdown --replace --index 1

# Translate document (preserves formatting)
godri docs translate "DOCUMENT_ID" "fr" --source-language "en"
godri docs translate "DOCUMENT_ID" "es" --start-index 10 --end-index 100
```

### Google Sheets Operations

#### Create Spreadsheet
```bash
godri sheets create-document "Spreadsheet Title" --folder-id "FOLDER_ID"
```

#### Sheet Management
```bash
# List all sheets in spreadsheet
godri sheets read "SPREADSHEET_ID"

# Create new sheet
godri sheets create "SPREADSHEET_ID" "Sheet Name"

# Hide/unhide sheets
godri sheets hide "SPREADSHEET_ID" "Sheet Name"
godri sheets unhide "SPREADSHEET_ID" "Sheet Name"

# Delete sheet
godri sheets delete "SPREADSHEET_ID" "Sheet Name"
```

#### Values Operations
```bash
# Read sheet data
godri sheets values read "SPREADSHEET_ID" --sheet-name "Sheet1" --range "A1:C10" --json --limit 100

# Set values
godri sheets values set "SPREADSHEET_ID" "A1:B2" "Value1,Value2,Value3,Value4"
godri sheets values set "SPREADSHEET_ID" "A1" '[[\"Row1Col1\",\"Row1Col2\"],[\"Row2Col1\",\"Row2Col2\"]]'

# Set formula
godri sheets values set "SPREADSHEET_ID" "C1" "SUM(A1:B1)" --formula

# Set values with formatting
godri sheets values set "SPREADSHEET_ID" "A1" "Bold Text" --format '{"textFormat":{"bold":true}}'

# Format cells (using JSON) - Basic examples
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"backgroundColor":{"red":1.0,"green":0.8,"blue":0.8}}'

# Copy formatting from another range
godri sheets values format "SPREADSHEET_ID" "A1:B5" --from "C1:C1"

# Copy single cell format to larger range (pattern replication)
godri sheets values format "SPREADSHEET_ID" "A1:E10" --from "A1"

# Copy multi-cell pattern with tiling
godri sheets values format "SPREADSHEET_ID" "A1:F10" --from "A1:B2"
```

#### Comprehensive Formatting Examples

**Font and Text Styling:**
```bash
# Set font family to Arial
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"fontFamily":"Arial"}}'

# Set font family to Calibri
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"fontFamily":"Calibri"}}'

# Make text bold
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"bold":true}}'

# Make text italic
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"italic":true}}'

# Make text underlined
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"underline":true}}'

# Set font size to 14pt
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"fontSize":14}}'
```

**Colors (RGB values from 0.0 to 1.0):**
```bash
# Red text
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"foregroundColor":{"red":1.0,"green":0.0,"blue":0.0}}}'

# Blue text
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"foregroundColor":{"red":0.0,"green":0.0,"blue":1.0}}}'

# Green text
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"foregroundColor":{"red":0.0,"green":0.8,"blue":0.0}}}'

# Yellow background
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"backgroundColor":{"red":1.0,"green":1.0,"blue":0.0}}'

# Light blue background
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"backgroundColor":{"red":0.8,"green":0.9,"blue":1.0}}'

# Light gray background
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"backgroundColor":{"red":0.9,"green":0.9,"blue":0.9}}'
```

**Combined Formatting:**
```bash
# Header style: bold Arial 12pt with gray background
godri sheets values format "SPREADSHEET_ID" "A1:E1" --format-options '{"textFormat":{"bold":true,"fontFamily":"Arial","fontSize":12},"backgroundColor":{"red":0.8,"green":0.8,"blue":0.8}}'

# Error style: bold red text with light red background
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"bold":true,"foregroundColor":{"red":1.0,"green":0.0,"blue":0.0}},"backgroundColor":{"red":1.0,"green":0.9,"blue":0.9}}'

# Success style: italic green text with light green background
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"italic":true,"foregroundColor":{"red":0.0,"green":0.6,"blue":0.0}},"backgroundColor":{"red":0.9,"green":1.0,"blue":0.9}}'

# Professional style: Calibri 11pt, center aligned
godri sheets values format "SPREADSHEET_ID" "A1:B5" --format-options '{"textFormat":{"fontFamily":"Calibri","fontSize":11},"horizontalAlignment":"CENTER"}'
```

#### Row/Column Operations
```bash
# Add/remove rows
godri sheets rows add "SPREADSHEET_ID" 5 --count 2 --sheet-name "Sheet1"
godri sheets rows remove "SPREADSHEET_ID" 5 --count 2 --sheet-name "Sheet1"

# Add/remove columns  
godri sheets columns add "SPREADSHEET_ID" "C" --count 1 --sheet-name "Sheet1"
godri sheets columns remove "SPREADSHEET_ID" "C" --count 1 --sheet-name "Sheet1"
```

#### Copy Sheets Between Spreadsheets
```bash
# Copy single sheet to another spreadsheet
godri sheets copy "SOURCE_SPREADSHEET_ID" "TARGET_SPREADSHEET_ID" "Sheet Name"

# Copy single sheet with custom target name
godri sheets copy "SOURCE_SPREADSHEET_ID" "TARGET_SPREADSHEET_ID" "Sheet1" --target-name "Copy of Sheet1"

# Copy multiple sheets
godri sheets copy "SOURCE_SPREADSHEET_ID" "TARGET_SPREADSHEET_ID" "Sheet1" "Sheet2" "Data"

# Copy sheets without preserving formatting
godri sheets copy "SOURCE_SPREADSHEET_ID" "TARGET_SPREADSHEET_ID" "Sheet1" --no-preserve-formatting
```

**Copy Features:**
- **Single Sheet Copy:** Copy individual sheets with optional custom naming
- **Multiple Sheet Copy:** Copy multiple sheets in one operation with batch processing
- **Format Preservation:** Maintains all cell formatting, styles, and structure by default
- **Name Collision Handling:** Automatically handles duplicate names with numbering (e.g., "Sheet1 (Copy)", "Sheet1 (Copy) (1)")
- **Error Reporting:** Detailed success/failure reporting for each sheet in batch operations
- **Google Sheets API Integration:** Uses native copyTo API for reliable sheet duplication

#### Translation Operations
```bash
# Translate range (preserves formulas and formatting)
godri sheets translate "SPREADSHEET_ID" "A1:C10" "fr" --source-language "en"

# Translate headers
godri sheets translate "SPREADSHEET_ID" "A1:Z1" "es"

# Translate specific sheet range
godri sheets translate "SPREADSHEET_ID" "Sheet1!B2:D20" "de"
```

**Translation Features:**
- **Format Preservation**: All cell formatting (bold, colors, etc.) is maintained during translation
- **Formula Intelligence**: Only string literals within formulas are translated, formula structure preserved
- **Smart Detection**: Automatically skips numbers, dates, and non-translatable content
- **Range Support**: Translate specific ranges or entire sheet areas

**Format Operations:**
- **JSON Formatting**: Apply custom formatting using Google Sheets format JSON
- **Format Copying**: Copy formatting from one range to another with intelligent tiling
- **Pattern Replication**: Single cell formatting can be copied to larger ranges

### Google Slides Operations

#### Create Presentation
```bash
# Create presentation with default theme (Streamline)
godri slides create-document "Presentation Title" --folder-id "FOLDER_ID"

# Create presentation with specific theme
godri slides create-document "Presentation Title" --theme "CORAL" --folder-id "FOLDER_ID"
```

**Available Themes:**
- SIMPLE_LIGHT, SIMPLE_DARK, STREAMLINE (default), FOCUS, SHIFT, MOMENTUM
- PARADIGM, SLATE, CORAL, BEACH_DAY, MODERN_WRITER, SPEARMINT
- GAMEDAY, BLUE_AND_YELLOW, SWISS, LUXE, MARINA, FOREST

#### Theme Management
```bash
# Import theme from another presentation
godri slides themes import "TARGET_PRESENTATION_ID" "SOURCE_PRESENTATION_ID"

# Import and automatically apply theme
godri slides themes import "TARGET_PRESENTATION_ID" "SOURCE_PRESENTATION_ID" --set

# Set theme for presentation
godri slides themes set "PRESENTATION_ID" "STREAMLINE"
```

#### Layout Operations
```bash
# List available slide layouts
godri slides layout list "PRESENTATION_ID"
```

**Available Layouts:**
- BLANK, CAPTION_ONLY, TITLE, TITLE_AND_BODY, TITLE_AND_TWO_COLUMNS
- TITLE_ONLY, SECTION_HEADER, SECTION_TITLE_AND_DESCRIPTION
- ONE_COLUMN_TEXT, MAIN_POINT, BIG_NUMBER

#### Slide Management
```bash
# Add slide with default layout (BLANK)
godri slides add "PRESENTATION_ID"

# Add slide with specific layout
godri slides add "PRESENTATION_ID" --layout "TITLE_AND_BODY"

# Add slide at specific position (0-based)
godri slides add "PRESENTATION_ID" --layout "TITLE" --position 2

# Move slide to new position
godri slides move "PRESENTATION_ID" "SLIDE_ID" 3

# Remove slide
godri slides remove "PRESENTATION_ID" "SLIDE_ID"
```

#### Content Management

**Enhanced Content Listing with Slide Number Support:**
```bash
# List content in specific slide by number (user-friendly)
godri slides content list "PRESENTATION_ID" 2

# List content in specific slide by API object ID (for precision)
godri slides content list "PRESENTATION_ID" "SLIDES_API1220751402_0"

# List content in multiple specific slides
godri slides content list "PRESENTATION_ID" 1 2 3

# List content for all slides in presentation
godri slides content list "PRESENTATION_ID" --all
godri slides content list "PRESENTATION_ID"  # empty slides list = all slides

# Show detailed formatting and properties
godri slides content list "PRESENTATION_ID" 2 --detailed
```

**Content Display Features:**
- **Text Content**: Shows actual text with formatting (bold, italic, font, size, color)
- **Size & Position**: Element dimensions and coordinates in EMU units
- **Shape Properties**: Background colors, borders, shape types
- **Table Contents**: Row-by-row table cell contents (shows empty cells)
- **Image Properties**: Content URLs and source URLs
- **Text Formatting**: Font family, size, style attributes
- **Detailed Mode**: Additional scaling factors and advanced properties

**Adding Content:**
```bash
# Add text content
godri slides content add "PRESENTATION_ID" "SLIDE_ID" text "Hello World" --x 100 --y 100 --width 300 --height 50

# Add text with formatting (similar to sheets formatting)
godri slides content add "PRESENTATION_ID" "SLIDE_ID" text "Bold Title" --format '{"textFormat":{"bold":true,"fontSize":18}}'

# Add image content
godri slides content add "PRESENTATION_ID" "SLIDE_ID" image "https://example.com/image.jpg" --x 200 --y 150 --width 400 --height 300

# Add table content (3 rows x 4 columns)
godri slides content add "PRESENTATION_ID" "SLIDE_ID" table "3x4" --x 50 --y 100 --width 500 --height 200

# Remove content element
godri slides content remove "PRESENTATION_ID" "ELEMENT_ID"

# Move content element
godri slides content move "PRESENTATION_ID" "ELEMENT_ID" 250 300
```

**Content Formatting Options:**
Slides support similar formatting options to Google Sheets:
```bash
# Bold text with blue color
--format '{"textFormat":{"bold":true,"foregroundColor":{"red":0.0,"green":0.0,"blue":1.0}}}'

# Large font with background color
--format '{"textFormat":{"fontSize":24,"fontFamily":"Arial"},"backgroundColor":{"red":0.9,"green":0.9,"blue":1.0}}'

# Combined formatting
--format '{"textFormat":{"bold":true,"italic":true,"fontSize":16,"fontFamily":"Calibri","foregroundColor":{"red":0.2,"green":0.2,"blue":0.8}}}'
```

#### Download Presentation
```bash
# Download entire presentation as PDF
godri slides download "PRESENTATION_ID" "/path/to/presentation.pdf" pdf

# Download entire presentation as PowerPoint
godri slides download "PRESENTATION_ID" "/path/to/presentation.pptx" pptx

# Download specific slides as PDF (slides 1-3)
godri slides download "PRESENTATION_ID" "/path/to/presentation.pdf" pdf --range "1-3"

# Download selected slides as PDF (slides 1, 3, and 5)
godri slides download "PRESENTATION_ID" "/path/to/presentation.pdf" pdf --range "1,3,5"

# Download multiple ranges as PPTX (slides 2-4 and 6-8)
godri slides download "PRESENTATION_ID" "/path/to/presentation.pptx" pptx --range "2-4,6-8"

# Download all slides as PNG images to directory
godri slides download "PRESENTATION_ID" "/path/to/images/" png

# Download specific slides as JPEG images (slides 1-5)
godri slides download "PRESENTATION_ID" "/path/to/images/" jpeg --range "1-5"
```

**Download Features:**
- **PDF Export:** Complete presentation or specific slides as PDF document
- **PPTX Export:** Native PowerPoint format with full fidelity
- **Image Export:** Individual slides as PNG or JPEG files with numbered filenames
- **Range Support:** Flexible slide selection (ranges, individual slides, multiple ranges)
- **Directory Creation:** Automatic creation of output directories for images
- **File Naming:** Images saved as `slide_001.png`, `slide_002.png`, etc.

#### Copy Slides Between Presentations
```bash
# Copy single slide from source to target presentation
godri slides copy "SOURCE_PRESENTATION_ID" "TARGET_PRESENTATION_ID" 2

# Copy multiple specific slides
godri slides copy "SOURCE_PRESENTATION_ID" "TARGET_PRESENTATION_ID" 1 3 5

# Copy range of slides (slides 1-3)
godri slides copy "SOURCE_PRESENTATION_ID" "TARGET_PRESENTATION_ID" "1-3"

# Copy complex range (slides 1-3 and slide 5)
godri slides copy "SOURCE_PRESENTATION_ID" "TARGET_PRESENTATION_ID" "1-3,5"

# Copy slides without preserving theme (use target presentation theme)
godri slides copy "SOURCE_PRESENTATION_ID" "TARGET_PRESENTATION_ID" "1-3" --no-preserve-theme

# Copy slides with source linking (maintain connection to source)
godri slides copy "SOURCE_PRESENTATION_ID" "TARGET_PRESENTATION_ID" "2-4" --link-to-source

# Copy slides to specific position in target presentation
godri slides copy "SOURCE_PRESENTATION_ID" "TARGET_PRESENTATION_ID" "1,2" --position 1
```

**Copy Features:**
- **Range Support:** Copy slides using ranges (1-3), individual numbers (2), or combinations (1-3,5)
- **Theme Preservation:** Maintains original formatting and theme by default
- **Source Linking:** Optional linking to maintain connection with source presentation
- **Position Control:** Insert copied slides at specific position or append to end
- **Batch Operations:** Copy multiple slides or ranges in single operation

**Range Format Examples:**
- `"1-3"` - Slides 1 through 3
- `"1,3,5"` - Slides 1, 3, and 5 only  
- `"2-4,6-8"` - Slides 2-4 and slides 6-8
- `"1,3-5,7"` - Slide 1, slides 3-5, and slide 7

### Google Forms Operations

**IMPORTANT: All section and question numbers use 1-based indexing (start from 1, not 0).**

#### Read Operations
```bash
# Get complete form structure
godri forms read form "FORM_ID"

# List all sections with question counts
godri forms read sections "FORM_ID"

# Get all questions from the form
godri forms read questions "FORM_ID"

# Get specific question by number (1-based)
godri forms read question "FORM_ID" 5

# Get all questions from specific section (1-based)
godri forms read section-questions "FORM_ID" 3
```

#### Write Operations
```bash
# Add new section
godri forms write add-section "FORM_ID" "Training Questions" --description "Questions about training" --position end

# Add new question to section (1-based)
godri forms write add-question "FORM_ID" "What is your experience level?" --type choice --section-index 2 --required --options "Beginner,Intermediate,Advanced"

# Add text question
godri forms write add-question "FORM_ID" "Please describe your background" --type text --section-index 1

# Update existing question (1-based question number)
godri forms write update-question "FORM_ID" 5 --title "Updated question title" --required

# Update section (1-based section number)
godri forms write update-section "FORM_ID" 2 --title "New Section Title" --description "Updated description"

# Remove question (1-based question number)
godri forms write remove-question "FORM_ID" 8

# Remove section (1-based section number) - removes all questions in section
godri forms write remove-section "FORM_ID" 3
```

#### Translation Operations
```bash
# Translate question and its options (1-based question number)
godri forms translate question "FORM_ID" 5 "fr" --translate-answers

# Translate without translating answer options
godri forms translate question "FORM_ID" 3 "es" --no-translate-answers

# Translate with specific source language
godri forms translate question "FORM_ID" 2 "de" --source-language "en"
```

**Forms Features:**
- **Complete CRUD Operations**: Read, create, update, delete forms, sections, and questions
- **1-Based Numbering**: User-friendly numbering for sections and questions (Training = Section 7, not 6)
- **Section Management**: Add, update, remove sections with positioning control
- **Question Types**: Support for text, choice, scale, date, time, and file upload questions
- **Translation Support**: Translate questions and answer options while preserving structure
- **Positioning Control**: Insert sections and questions at specific positions (before/after/end)
- **Data Validation**: Required/optional question settings and proper form validation

**Numbering Examples:**
- Section 1 = Default Section, Section 7 = Training (user-facing numbers)
- Question 1 = First question, Question 20 = "Are you trained in IP?" (user-facing numbers)
- All CLI and MCP tools automatically convert to internal 0-based indexing

### Translation

```bash
# Translate text (auto-detect source)
godri translate "Hello, world!" "fr"

# Translate with specified source language
godri translate "Bonjour le monde!" "en" --source-language "fr"
```

## Advanced Examples

### Complex Slides Operations
```bash
# Create presentation with corporate theme and add structured content
PRES_ID=$(godri slides create-document "Sales Presentation" --theme "LUXE" | grep -o 'ID: [^,]*' | cut -d' ' -f2)

# Add title slide
godri slides add "$PRES_ID" --layout "TITLE" --position 0
TITLE_SLIDE=$(godri slides content list "$PRES_ID" | head -1 | cut -d' ' -f4)  # Get first slide ID

# Add content to title slide
godri slides content add "$PRES_ID" "$TITLE_SLIDE" text "Q4 Sales Results" --x 100 --y 150 --width 600 --height 100 --format '{"textFormat":{"bold":true,"fontSize":32,"fontFamily":"Arial"}}'

# Add content slide with data
godri slides add "$PRES_ID" --layout "TITLE_AND_BODY"
CONTENT_SLIDE=$(godri slides content list "$PRES_ID" | tail -1 | cut -d' ' -f4)  # Get last slide ID

# Add table with sales data
godri slides content add "$PRES_ID" "$CONTENT_SLIDE" table "4x3" --x 50 --y 200 --width 600 --height 300

# List all content for review
godri slides content list "$PRES_ID" "$TITLE_SLIDE"
godri slides content list "$PRES_ID" "$CONTENT_SLIDE"
```

### Complex Sheet Operations
```bash
# Create spreadsheet and add data with formulas
SHEET_ID=$(godri sheets create-document "Sales Report" | grep -o 'ID: [^,]*' | cut -d' ' -f2)
godri sheets values set "$SHEET_ID" "A1:C1" "Product,Price,Total"
godri sheets values set "$SHEET_ID" "A2:B3" "Widget,10,Gadget,20"
godri sheets values set "$SHEET_ID" "C2" "B2*2" --formula
godri sheets values set "$SHEET_ID" "C3" "B3*2" --formula
godri sheets values format "$SHEET_ID" "A1:C1" '{"textFormat":{"bold":true}}'

# Translate to multiple languages
godri sheets translate "$SHEET_ID" "A1:A3" "fr"  # Translate product names to French
godri sheets translate "$SHEET_ID" "A1:C1" "es"  # Translate headers to Spanish
```

### Translation Workflow
```bash
# Translate Google Doc to French
godri docs translate "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms" "fr"

# Translate specific range in spreadsheet
godri sheets translate "1n0lrRoYg6KW7uoyGuawe88XSY5o5dF9dkwAFCmnregs" "A1:C10" "de" --source-language "en"

# Translate document section (characters 100-500)
godri docs translate "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms" "es" --start-index 100 --end-index 500
```

### Batch File Operations
```bash
# Upload multiple files to same folder
for file in *.txt; do
    godri drive upload "$file" --folder-id "FOLDER_ID"
done
```

## MCP (Model Context Protocol) Server

Godri includes an MCP server that provides Google Workspace integration for AI assistants and other applications.

### Starting the MCP Server

```bash
# Start MCP server with stdio transport (for Claude Desktop and other MCP clients)
godri mcp --transport stdio

# Start MCP server with HTTP transport (for web applications)
godri mcp --transport http --host localhost --port 8000
```

### Available MCP Tools

**Enhanced Slides Content Tools:**
- `slides_content_list(presentation_id, slide_identifiers="", all_slides=False)` - List detailed content in slides with enhanced formatting information
  - Supports slide numbers (1, 2, 3), API object IDs, or ranges (1-3,5)
  - Set `all_slides=True` to list content for all slides
  - Returns detailed text content, formatting, size, position, and properties

**Copy Tools:**
- `slides_copy(source_presentation_id, target_presentation_id, slide_identifiers, preserve_theme=True, link_to_source=False, target_position=-1)` - Copy slides between presentations
  - Supports ranges like "1-3,5" or individual slides "2"
  - Optional theme preservation and source linking
  - Position -1 adds at end, or specify target position
- `sheets_copy(source_spreadsheet_id, target_spreadsheet_id, sheet_names, target_name="", preserve_formatting=True)` - Copy sheets between spreadsheets
  - Comma-separated sheet names for multiple sheet copy
  - Optional custom target name for single sheet
  - Formatting preservation with collision handling

**Drive Tools:**
- `drive_search(query, name, mime_type, limit)` - Search files and folders
- `drive_upload(file_path, folder_id, name)` - Upload files
- `drive_download(file_id, output_path, smart)` - Download files with smart conversion
- `drive_folder_create(name, parent_id)` - Create folders
- `drive_folder_delete(file_id)` - Delete files/folders

**Docs Tools:**
- `docs_createdocument(title, folder_id, content, markdown)` - Create documents
- `docs_read(document_id, plain_text)` - Read document content
- `docs_update(document_id, content, markdown, replace, index)` - Update documents
- `docs_translate(document_id, target_language, source_language, start_index, end_index)` - Translate documents

**Sheets Tools:**
- `sheets_createdocument(title, folder_id)` - Create spreadsheets
- `sheets_read(spreadsheet_id)` - List sheets
- `sheets_values_read(spreadsheet_id, sheet_name, range_name)` - Read data
- `sheets_values_set(spreadsheet_id, range_name, values, formula)` - Set values
- `sheets_translate(spreadsheet_id, range_name, target_language, source_language)` - Translate ranges

**Slides Tools:**
- `slides_createdocument(title, folder_id, theme)` - Create presentations
- `slides_download(presentation_id, format_type, output_path)` - Download presentations
- `slides_add(presentation_id, layout, position)` - Add slides
- `slides_content_add(presentation_id, slide_id, content_type, content, x, y, width, height)` - Add content

**Forms Tools (1-based numbering):**
- `forms_get_form(form_id)` - Get complete form structure with metadata
- `forms_get_sections(form_id)` - List all sections with question counts and navigation
- `forms_get_questions(form_id)` - Get all questions organized by sections
- `forms_get_question(form_id, question_number)` - Get specific question details (1-based)
- `forms_get_section_questions(form_id, section_index)` - Get questions from specific section (1-based)
- `forms_add_section(form_id, title, description, position, reference_question)` - Add new section
- `forms_add_question(form_id, title, question_type, description, required, section_index, position, reference_question, options)` - Add new question (1-based section)
- `forms_update_question(form_id, question_number, title, description, question_type, required, options)` - Update question (1-based)
- `forms_update_section(form_id, section_index, title, description, go_to_action, go_to_section_id)` - Update section (1-based)
- `forms_remove_question(form_id, question_number)` - Remove question (1-based)
- `forms_remove_section(form_id, section_index)` - Remove section and all questions (1-based)
- `forms_translate_question(form_id, question_number, target_language, translate_answers, source_language)` - Translate question (1-based)

**Translation Tools:**
- `translate_text(text, target_language, source_language)` - Translate text

### MCP Configuration

The MCP server automatically uses the same authentication as the CLI. Ensure you've run `godri auth` before starting the MCP server.

## Development

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
└── README.md
```

### Code Quality
```bash
# Format code (required before commits)
black -l 120 src/

# Run application
godri <command>
```

## Common MIME Types

| File Type | MIME Type |
|-----------|-----------|
| Google Doc | `application/vnd.google-apps.document` |
| Google Sheet | `application/vnd.google-apps.spreadsheet` |
| Google Slides | `application/vnd.google-apps.presentation` |
| Google Folder | `application/vnd.google-apps.folder` |
| PDF | `application/pdf` |
| Text | `text/plain` |
| Word | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Excel | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

## Error Handling & Debugging

- Use `--verbose` flag for detailed logging
- Authentication tokens stored in `~/.godri-token.json`
- Comprehensive error messages with actionable guidance
- Automatic retry logic for transient API errors

## Security

- OAuth2 tokens stored securely in user home directory
- Client secret file should never be committed to version control
- All API communication uses HTTPS
- Tokens automatically refresh when expired

## Support

For issues, feature requests, or questions:
1. Check the command help: `godri <command> --help`
2. Enable verbose logging: `godri --verbose <command>`
3. Verify API quotas in Google Cloud Console
4. Ensure all required APIs are enabled

## Integration with AI Assistants

### Claude Code Integration

You can integrate Godri with Claude Code to enable AI assistant access to your Google Workspace documents and data.

#### Option 1: MCP Server Integration (Recommended)

1. **Install Godri as a package:**
   ```bash
   git clone https://github.com/sebastienmorand-loreal/godri.git
   cd godri
   uv install .
   ```

2. **Set up authentication:**
   ```bash
   export GODRI_CLIENT_FILE="/path/to/your/client_secret.json"
   godri auth
   ```

3. **Configure Claude Code to use the MCP server:**
   Add to your Claude Code configuration (`~/.claude/mcp_servers.json`):
   ```json
   {
     "godri": {
       "command": "godri",
       "args": ["mcp", "stdio"]
     }
   }
   ```

4. **Start using Godri tools in Claude:**
   After configuration, Claude Code will have access to all Godri MCP tools:
   - Drive operations (search, upload, download, smart conversion)
   - Document operations (create, read, update, translate)
   - Spreadsheet operations (create, read sheets, manage values, formatting, translation)
   - Presentation operations (create, add slides, manage content, download, copy)
   - Translation services

#### Option 2: Development Mode Integration

For development or if you prefer to run from source:

1. **Clone this repository:**
   ```bash
   git clone https://github.com/sebastienmorand-loreal/godri.git
   cd godri
   uv sync
   uv install -e .  # Install in editable mode
   ```

2. **Set up authentication:**
   ```bash
   export GODRI_CLIENT_FILE="/path/to/your/client_secret.json"
   godri auth
   ```

3. **Configure Claude Code (same as Option 1):**
   Add to your Claude Code configuration (`~/.claude/mcp_servers.json`):
   ```json
   {
     "godri": {
       "command": "godri",
       "args": ["mcp", "stdio"]
     }
   }
   ```

4. **Use with Claude Code:**
   - Open the repository in Claude Code for development
   - Claude can read your code and help with development
   - Use Claude to run commands like: `godri drive search --name "document"`

#### Setup Verification

To verify your installation works correctly:

1. **Test CLI access:**
   ```bash
   godri --help
   godri drive search --name "test" --limit 5
   ```

2. **Test MCP server:**
   ```bash
   godri mcp stdio
   # Should start the MCP server and wait for input
   ```

3. **Restart Claude Code** after adding the MCP configuration to load the new tools.

### Gemini CLI Integration

Godri can be integrated with Google's Gemini CLI for enhanced AI-powered document analysis.

#### Setup for Gemini CLI

1. **Install Gemini CLI:**
   ```bash
   pip install google-generativeai
   ```

2. **Create a wrapper script** (`gemini-godri.py`):
   ```python
   #!/usr/bin/env python3
   import subprocess
   import sys
   import json
   
   def run_godri_command(args):
       """Run godri command and return results"""
       try:
           result = subprocess.run(
               ['godri'] + args,
               capture_output=True,
               text=True
           )
           return result.stdout
       except Exception as e:
           return f"Error: {e}"
   
   # Example: Search and analyze documents
   if __name__ == "__main__":
       if len(sys.argv) > 1 and sys.argv[1] == "analyze-docs":
           # Search for documents
           docs = run_godri_command(['drive', 'search', '--name', sys.argv[2], '--limit', '10'])
           print(f"Found documents: {docs}")
           
           # Use Gemini to analyze document content
           # Add your Gemini analysis logic here
   ```

3. **Usage examples:**
   ```bash
   # Search and analyze documents
   python gemini-godri.py analyze-docs "quarterly report"
   
   # Translate documents with AI assistance
   python gemini-godri.py translate-with-ai "document_id" "target_language"
   ```

#### Advanced Gemini Integration

Create specialized scripts for common workflows:

1. **Document Analysis Script:**
   ```python
   # Use godri to read documents, Gemini to analyze content
   doc_content = run_godri_command(['docs', 'read', document_id, '--plain-text'])
   # Send to Gemini for analysis
   ```

2. **Intelligent Translation:**
   ```python
   # Use godri to read, Gemini to improve translation, godri to update
   original = run_godri_command(['docs', 'read', document_id])
   # Gemini analysis for context-aware translation
   # Update with godri
   ```

3. **Smart Spreadsheet Analysis:**
   ```python
   # Use godri to read spreadsheet data
   data = run_godri_command(['sheets', 'values', 'read', spreadsheet_id, '--json'])
   # Use Gemini for data analysis and insights
   ```

### Benefits of AI Integration

- **Document Intelligence:** AI can analyze document content and suggest improvements
- **Smart Search:** Use natural language to find documents across Google Drive
- **Automated Translation:** Context-aware translation with formatting preservation
- **Data Analysis:** Intelligent analysis of spreadsheet data and presentation content
- **Workflow Automation:** Combine godri operations with AI decision-making

### Security Considerations

- The MCP server inherits the same OAuth2 authentication as the CLI
- All Google API communication remains secure (HTTPS)
- AI assistants only have access to tools you explicitly enable
- Consider using read-only operations for sensitive documents

## License

Personal/Educational use. Ensure compliance with Google API Terms of Service.