# BROOK Compliance Checker - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Code Analysis & Changes](#code-analysis--changes)
4. [Compliance Pattern Matching](#compliance-pattern-matching)
5. [Document Processing](#document-processing)
6. [Rule Structure & JSON Format](#rule-structure--json-format)
7. [Troubleshooting & Debugging](#troubleshooting--debugging)
8. [Usage Instructions](#usage-instructions)
9. [Future Enhancements](#future-enhancements)

---

## Project Overview

The BROOK Compliance Checker is an automated tool designed to verify that BROOK Aviation's operational documents comply with their Air Operator Certificate (AOC) and Operations Specifications (OpsSpecs). The system analyzes multiple document types including:

- **OM-A**: Operations Manual Part A (Generic/Basic)
- **OM-B**: Operations Manual Part B (Helicopter Operating Matters)
- **OM-C**: Operations Manual Part C (Route/Area/Aerodrome Guidance)
- **OM-D**: Operations Manual Part D (Training Manual)
- **MEL**: Minimum Equipment List
- **MCM**: Maintenance Control Manual
- **SMS**: Safety Management System Manual
- **ERP**: Emergency Response Plan
- **AOC**: Air Operator Certificate
- **OpsSpecs**: Operations Specifications

---

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Source Docs   │    │  Compliance      │    │   Excel Report  │
│   (DOCX/PDF)    │───▶│  Rules (JSON)    │───▶│   (Results)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  Text Extractor │    │  Pattern Matcher │
│  (docx/PyPDF2)  │    │  (contains_any) │
└─────────────────┘    └──────────────────┘
```

---

## Code Analysis & Changes

### 1. Main Compliance Checker (`run_compliance_check.py`)

**Purpose**: Core script that orchestrates the entire compliance checking process.

**Key Functions**:

#### `load_text_from_doc(path: Path) -> str`
- **What it does**: Extracts text from different document formats
- **Supported formats**: DOCX, PDF, TXT, MD
- **Process**:
  - For DOCX: Uses `python-docx` library to extract paragraph text
  - For PDF: Uses `PyPDF2` to extract text from each page
  - For TXT/MD: Direct text reading with UTF-8 encoding
- **Error handling**: Gracefully handles extraction failures and returns empty string

#### `main(rules_json_path: str, output_xlsx_path: str)`
- **What it does**: Main orchestration function
- **Process**:
  1. Loads JSON rules file
  2. Creates text cache for all documents
  3. Processes each rule against relevant documents
  4. Generates Excel report with results

**Pattern Matching Logic**:
```python
# For each rule, check if ANY pattern matches
for chk in checks:
    t = chk.get("type")
    patterns = chk.get("patterns", [])
    if t == "contains_any":
        for pat in patterns:
            if pat and pat.lower() in doc_text.lower():
                found = True
                matched_pattern = pat
                break
```

### 2. Debug Script (`debug_text_extraction.py`)

**Purpose**: Diagnostic tool to troubleshoot text extraction and pattern matching issues.

**Key Features**:
- **Detailed logging**: Shows exactly what text is extracted from each document
- **Pattern testing**: Tests individual patterns against document content
- **Document statistics**: Reports paragraph/page counts and text lengths
- **Visual feedback**: Uses ✓/✗ symbols to show pattern match results

**Usage**: Run this script to see exactly what's happening during text extraction and why rules might be failing.

### 3. Report Analyzer (`analyze_report.py`)

**Purpose**: Simple utility to analyze generated compliance reports.

**Features**:
- **Summary statistics**: Total rules, found vs missing counts
- **Detailed results**: Lists each rule and its compliance status
- **Missing rules**: Highlights any non-compliant items

---

## Compliance Pattern Matching

### Pattern Types

The system currently supports one pattern type:

#### `contains_any`
- **Logic**: Rule passes if ANY of the specified patterns are found in the document
- **Implementation**: Case-insensitive substring search
- **Example**:
```json
{
  "type": "contains_any",
  "patterns": [
    "Aircraft",
    "model", 
    "S-76",
    "4X-BHS",
    "4X-BEX"
  ]
}
```

### Pattern Matching Strategy

1. **Text Normalization**: All text is converted to lowercase for comparison
2. **Substring Search**: Uses Python's `in` operator for pattern matching
3. **Multiple Document Support**: Combines text from all source documents before searching
4. **First Match Wins**: Stops searching once any pattern is found

### Why This Approach Works

- **Regulatory Compliance**: Aviation regulations often use specific, standardized terminology
- **Document Consistency**: Company manuals typically use consistent language
- **Flexibility**: Multiple patterns allow for variations in how requirements are expressed
- **Performance**: Simple substring search is fast and reliable

---

## Document Processing

### Text Extraction Process

#### DOCX Files
```python
from docx import Document
d = Document(str(path))
text = "\n".join(p.text for p in d.paragraphs)
```
- **Advantages**: Reliable text extraction, preserves formatting structure
- **Limitations**: May miss text in tables, headers, footers

#### PDF Files
```python
import PyPDF2
reader = PyPDF2.PdfReader(f)
pages = []
for p in reader.pages:
    pages.append(p.extract_text() or "")
text = "\n".join(pages)
```
- **Advantages**: Handles scanned documents, preserves page structure
- **Limitations**: Quality depends on PDF format (text vs image-based)

### Document Mapping

The system uses a hardcoded mapping between document keys and filenames:

```python
DOC_FILES = {
    "OpsSpecs": "Opspecs Brook BHSBEXBHT -BOB - 27-04-2025.pdf",
    "AOC": "AOC 23-24.pdf",
    "OM-A": "OMA - REV 05.docx",
    "OM-B": "OMB - REV 05.docx",
    "OM-C": "OMC  - REV 05.docx",
    "OM-D": "OMD - REV 05.docx",
    "MEL": "BROOK S-76 MEL 4X-BHS,BHP,BHT,BEX,BOB,BOA, BOI S76C++ Rev 6 (1 Aug 2025).docx",
    "MCM": "BROOK MCM REV 4 - 1 Aug 2025.docx",
    "SMS": "mod_Brook SMS Manual rev 0.docx",
    "ERP": "ERP Draft - Final (1) (1).docx",
}
```

---

## Rule Structure & JSON Format

### Rule Components

Each compliance rule contains:

```json
{
  "id": "unique_rule_identifier",
  "category": "rule_category",
  "item": "human_readable_description",
  "statement_from_opspecs": "exact_text_from_opspecs",
  "statement_from_aoc_or_om": "how_it_appears_in_company_docs",
  "interpreted_scope": "what_the_rule_means",
  "limitations_notes": "important_restrictions",
  "source_docs": ["list", "of", "relevant", "documents"],
  "locator_hint": "where_to_find_in_opspecs",
  "checks": [
    {
      "type": "contains_any",
      "patterns": ["pattern1", "pattern2", "pattern3"]
    }
  ],
  "evidence_hints": ["what", "to", "show", "for", "compliance"],
  "owner": "responsible_person/department",
  "verification_method": "how_to_verify_compliance"
}
```

### Rule Categories

1. **Fleet**: Aircraft type approvals, registrations
2. **Operations**: Types of operations (HEMS, etc.)
3. **Area**: Geographic limitations
4. **Limitations**: Flight rules, operational restrictions
5. **Specific Approvals**: NVG, RVSM, EDTO
6. **Other**: Special operational requirements
7. **Airworthiness**: Maintenance and continuing airworthiness

---

## Troubleshooting & Debugging

### Common Issues & Solutions

#### 1. All Rules Show as "MISSING"
**Symptoms**: Compliance report shows 0% compliance
**Causes**:
- Missing Python dependencies
- Document files not found
- Text extraction failures
- Pattern matching logic errors

**Solutions**:
- Install required packages: `pip install python-docx PyPDF2 pandas openpyxl`
- Verify all document files are present
- Run debug script to check text extraction
- Check pattern syntax in JSON rules

#### 2. Text Extraction Failures
**Symptoms**: Empty text from documents
**Causes**:
- Corrupted document files
- Unsupported document formats
- Permission issues
- Library compatibility problems

**Solutions**:
- Verify document integrity
- Check file permissions
- Update Python libraries
- Try alternative extraction methods

#### 3. Pattern Matching Issues
**Symptoms**: Rules not matching expected content
**Causes**:
- Incorrect pattern text
- Case sensitivity issues
- Special characters in patterns
- Text formatting differences

**Solutions**:
- Review pattern text carefully
- Use debug script to see extracted text
- Simplify patterns to basic keywords
- Check for hidden characters

### Debug Workflow

1. **Run debug script**: `python debug_text_extraction.py`
2. **Check text extraction**: Verify documents are loading correctly
3. **Test patterns**: See which patterns are matching/failing
4. **Review extracted text**: Look for formatting issues
5. **Adjust patterns**: Modify JSON rules as needed

---

## Usage Instructions

### Prerequisites

1. **Python 3.7+** installed
2. **Required packages**:
   ```bash
   pip install python-docx PyPDF2 pandas openpyxl
   ```
3. **All document files** in the same directory as scripts
4. **JSON rules file** properly formatted

### Basic Usage

1. **Run compliance check**:
   ```bash
   python run_compliance_check.py brook_rules_from_spec_patched.json brook_compliance_report.xlsx
   ```

2. **Debug issues**:
   ```bash
   python debug_text_extraction.py
   ```

3. **Analyze results**:
   ```bash
   python analyze_report.py
   ```

### File Organization

```
project_folder/
├── run_compliance_check.py          # Main compliance checker
├── debug_text_extraction.py         # Debug utility
├── analyze_report.py                # Report analyzer
├── brook_rules_from_spec_patched.json  # Compliance rules
├── brook_compliance_report.xlsx     # Generated report
├── OMA - REV 05.docx               # Operations Manual A
├── OMB - REV 05.docx               # Operations Manual B
├── OMC  - REV 05.docx              # Operations Manual C
├── OMD - REV 05.docx               # Operations Manual D
├── BROOK S-76 MEL...docx           # Minimum Equipment List
├── BROOK MCM REV 4...docx          # Maintenance Control Manual
├── mod_Brook SMS Manual...docx      # Safety Management System
├── ERP Draft - Final...docx         # Emergency Response Plan
├── AOC 23-24.pdf                   # Air Operator Certificate
└── Opspecs Brook...pdf             # Operations Specifications
```

---

## Future Enhancements

### Advanced Pattern Matching

1. **Regular Expressions**: Support for complex pattern matching
2. **Fuzzy Matching**: Handle typos and variations
3. **Semantic Analysis**: Understand context and meaning
4. **Confidence Scoring**: Rate pattern match quality

### Enhanced Document Processing

1. **Table Extraction**: Better handling of tabular data
2. **Image OCR**: Extract text from scanned images
3. **Format Preservation**: Maintain document structure
4. **Version Control**: Track document changes over time

### Reporting Improvements

1. **Risk Assessment**: Categorize compliance issues by severity
2. **Action Items**: Generate specific recommendations
3. **Trend Analysis**: Track compliance over time
4. **Dashboard**: Web-based compliance monitoring

### Integration Capabilities

1. **API Endpoints**: RESTful interface for external systems
2. **Database Storage**: Persistent compliance history
3. **Email Alerts**: Notify stakeholders of compliance issues
4. **Workflow Integration**: Connect with existing business processes

---

## Conclusion

The BROOK Compliance Checker provides a solid foundation for automated regulatory compliance verification. The system successfully:

- **Extracts text** from multiple document formats
- **Applies structured rules** to verify compliance
- **Generates clear reports** for stakeholders
- **Provides debugging tools** for troubleshooting

The pattern-based approach is well-suited for aviation compliance, where requirements are typically expressed in standardized terminology. The modular design allows for easy expansion and enhancement as requirements evolve.

For production use, consider implementing:
- **Error logging** and monitoring
- **Performance optimization** for large document sets
- **User interface** for non-technical users
- **Integration** with existing compliance management systems

---

## Support & Maintenance

- **Regular Updates**: Keep Python packages updated
- **Document Validation**: Verify document file integrity
- **Rule Maintenance**: Review and update compliance rules as regulations change
- **Performance Monitoring**: Track processing times and resource usage
- **User Training**: Ensure stakeholders understand the system capabilities and limitations

