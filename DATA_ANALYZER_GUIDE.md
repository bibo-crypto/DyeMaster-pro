# Data Analyzer Tool - Documentation

## Overview
The Data Analyzer is a new feature in the Color Chemistry Management System that allows you to upload and analyze production data from Excel files, similar to the "New Situazione" report in WNCOINT.xlsx.

## Features

### 1. File Upload
- Load Excel files (`.xlsx`) containing production data
- Currently supports WNCOINT.xlsx format with the following sheets:
  - Sheet1, Data prod., DFM, WINCOINT, Uscita(J), Qualita
  - New Situazione (reference template)

### 2. Analysis Types

#### Production Status
- Shows current status of all production batches
- Displays: Batch ID, Article, Color, Status, Date, Delivery Date
- Status determined from: Bagno, Tinto, C.Q, Custom fields

#### Quality Control Summary
- Analyzes QC (Quality Control) data
- Shows: Batch, Article, Color, QC Status, QC Date, Notes
- Only displays items with QC information

#### Complete Report (New Situazione)
- Generates comprehensive production report
- Includes all production details:
  - Client, Article, Title, Code, Color
  - Order details (Ordine, Riga)
  - Production dates and delivery
  - Batch number, Rocche (spools), M/C values
  - Production stages: Bagno, Tinto, C.Q (Quality Control)
  - Status and completion dates

### 3. Data Export
- Export analysis results to **Excel (.xlsx)** format
- Export analysis results to **CSV format**
- Preserves all columns and data formatting
- Auto-adjusts column widths for readability

## How to Use

### Opening the Data Analyzer
1. In the main application, go to **Tools menu**
2. Click **📊 Data Analyzer**
3. A new window will open with the analyzer interface

### Workflow

#### Step 1: Load File
1. Click "Choose Excel File" button
2. Select an Excel file (e.g., WNCOINT.xlsx)
3. File path will be displayed in the status line

#### Step 2: Configure Analysis
1. Select the analysis type:
   - **Production Status** - Quick overview of all items
   - **Quality Control Summary** - QC-specific data
   - **Complete Report** - Full production details like "New Situazione"

#### Step 3: Analyze
1. Click "Analyze Data" button
2. Progress bar will show analysis is running
3. Results appear in the table below

#### Step 4: Export (Optional)
1. Click "Export to Excel" or use Save dialog
2. Choose output format (.xlsx or .csv)
3. Specify filename and location
4. Results are saved to file

## Data Structure

### Source Files
The analyzer expects Excel files with these sheets:
- **Sheet1** - Basic product information
- **Data prod.** - Production data
- **DFM** - Dyeing machine formulas
- **WINCOINT** - Quality control data
- **Uscita(J)** - Exit/shipping data
- **Qualita** - Quality control details

### Key Fields
- **Partita** - Batch number (primary key)
- **Articolo** - Article code
- **Colore** - Color name
- **Ordine** - Order number
- **Data** - Production date
- **Consegna** - Delivery date
- **Bagno** - Dye bath code
- **Tinto** - Dyeing status
- **C.Q** - Quality control status
- **Custom** - Final status (e.g., "Spedita" = Shipped)

## Output Examples

### Production Status Record
```
Batch: 155179
Article: C010099S
Color: TENEBROSO
Status: In Production
Date: 2025-12-21
Delivery: 2026-01-09
```

### Quality Control Record
```
Batch: 154141
Article: C010034S
Color: @INCHIOSTRO
QC Status: OO
QC Date: 2025-12-22
Notes: PG-154123-PM-835686-FRESCOBOL
```

### Complete Report Record (All fields)
```
Cliente: MEDITERRANEAN
Articolo: C010099S
Titolo: 70/1
Codice: 1975
Colore: TENEBROSO
Ordine: 0/005074
Riga: 1
Data: 2025-12-21
Consegna: 2026-01-09
Partita: 155179
Rocche: 128
Bagno: (empty)
C.Q: OO
Tinto: (empty)
Data Qualita: (empty)
Data Uscita: (empty)
Custom: (empty)
...
```

## Technical Details

### File Locations
- **UI Component**: `ui/data_analyzer_window.py`
- **Analysis Engine**: `app/data_analyzer.py`
- **Integration Point**: `app/gui.py` (Tools menu)

### Classes

#### DataAnalyzer
- **Location**: `app/data_analyzer.py`
- **Methods**:
  - `__init__(file_path)` - Initialize with Excel file
  - `load_sheets()` - Load data from available sheets
  - `analyze_production_status()` - Production overview
  - `analyze_quality()` - Quality control analysis
  - `analyze_complete()` - Complete report
  - `export_to_excel(results, path)` - Save to Excel
  - `export_to_csv(results, path)` - Save to CSV

#### DataAnalyzerWindow
- **Location**: `ui/data_analyzer_window.py`
- **Methods**:
  - `setup_ui()` - Create interface components
  - `upload_file()` - File dialog and loading
  - `analyze_data()` - Run analysis
  - `display_results()` - Show results in table
  - `export_results()` - Export dialog

### Performance
- **Maximum rows displayed**: 500 (for performance)
- **Export limit**: Unlimited (Excel file size permitting)
- **Processing time**: < 1 second for typical files (100-200 records)

## Limitations

1. **File Size**: Works best with files < 10 MB
2. **Sheet Detection**: Requires standard sheet names
3. **Data Format**: Expects specific column headers matching WNCOINT.xlsx
4. **Excel Version**: Requires openpyxl-compatible xlsx files

## Future Enhancements

Potential features for future versions:
- [ ] Support for multiple file uploads and merging
- [ ] Advanced filtering and sorting in the results table
- [ ] Custom column selection before analysis
- [ ] Data validation and cleaning options
- [ ] Scheduled analysis and reports
- [ ] Database integration for historical tracking
- [ ] Chart and graph visualizations
- [ ] PDF report export

## Troubleshooting

### Issue: "File not found" error
**Solution**: Ensure the file path is correct and file exists

### Issue: No results displayed
**Solution**: 
- Check if the Excel file has the expected sheet names
- Verify data exists in the selected sheets

### Issue: Export fails
**Solution**: 
- Ensure output directory has write permissions
- Check available disk space
- Verify filename doesn't contain invalid characters

### Issue: Analysis takes too long
**Solution**: 
- Try analyzing smaller data sets first
- Export to CSV instead of Excel for large datasets

## Support

For issues or feature requests, contact the development team or file a bug report with:
1. Excel file sample (or description)
2. Error message or unexpected behavior
3. Steps to reproduce the issue
