# BROOK Compliance Checker

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An automated compliance verification tool that checks BROOK Aviation's operational documents for compliance with their Air Operator Certificate (AOC) and Operations Specifications (OpsSpecs). The system uses semantic pattern matching to provide evidence-based compliance decisions with confidence scoring.

## 🎯 Project Overview

The BROOK Compliance Checker automates the tedious process of manually verifying that company manuals align with regulatory requirements. It processes multiple document types and provides:

- **4-State Compliance Output**: FOUND, MISSING, CONFLICT, REVIEW
- **Evidence Collection**: Document snippets with confidence scoring
- **Conflict Detection**: Automatic identification of contradictory information
- **Audit Trail**: Complete evidence and reasoning for compliance decisions
- **Professional Reports**: Excel output suitable for regulatory review

## 🚀 Features

### Core Capabilities
- **Semantic Pattern Matching**: Positive patterns, negative patterns, forbidden claims
- **Multi-Document Support**: PDF, DOCX, TXT, MD file processing
- **OpsSpecs Alignment**: Automatic detection of fleet/area mismatches
- **Confidence Scoring**: 0.0-1.0 confidence based on evidence quality
- **Rule Types**: affirm, deny, limit, align_with_opspecs

### Document Types Supported
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

## 📋 Prerequisites

- **Python 3.8 or higher** (recommended: Python 3.9+)
- **pip** (Python package installer)
- **Git** (for cloning the repository)

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd "IFR Compliance"
```

### 2. Create a virtual environment (recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## 📁 Project Structure

```
IFR Compliance/
├── run_compliance_check_semantic.py    # Main semantic compliance checker
├── brook_semantic_rules.json          # Semantic rule definitions
├── ops_facts_brook.json               # Operational facts for validation
├── requirements.txt                    # Python package dependencies
├── SETUP_GUIDE.md                     # Detailed setup instructions
├── debug_text_extraction.py           # Document processing verification
├── analyze_report.py                  # Report analysis utility
├── COMPLIANCE_CHECKER_DOCUMENTATION.md # Technical documentation
├── QUICK_REFERENCE_GUIDE.md          # Quick reference guide
└── .venv/                            # Virtual environment
```

## 🚀 Usage

### Basic Compliance Check
```bash
python run_compliance_check_semantic.py brook_semantic_rules.json output_report.xlsx ops_facts_brook.json
```

### Analyze Existing Reports
```bash
python analyze_report.py
```

### Debug Document Processing
```bash
python debug_text_extraction.py
```

## 📊 Output Format

The Excel report contains comprehensive compliance information:

| Column | Description |
|--------|-------------|
| **Rule ID** | Unique identifier for each compliance rule |
| **Item** | Human-readable description of what's being checked |
| **Source docs** | Documents used for compliance verification |
| **Result** | One of FOUND/MISSING/CONFLICT/REVIEW |
| **Matched pattern** | First pattern that triggered a match |
| **Evidence (positive)** | Snippets supporting compliance |
| **Contradiction (if any)** | Evidence contradicting compliance |
| **Confidence** | 0.0-1.0 confidence score |
| **Locator hint** | Where to find the relevant information |
| **Owner** | Responsible party for the compliance item |
| **Evidence hints** | What evidence should be visible |
| **Notes** | Additional context and reasoning |

## ⚙️ Configuration

### Rule Structure
Rules are defined in JSON format with semantic patterns:

```json
{
  "id": "FLEET-S76-ALIGN",
  "category": "Fleet",
  "rule_type": "align_with_opspecs",
  "item": "Manuals list only the OpsSpecs-approved fleet",
  "positive_patterns": ["S-76C\\+\\+", "4X-BHS|4X-BEX|4X-BHT|4X-BOB"],
  "negative_patterns": ["\\b(not\\s+(authorized|allowed|approved)|prohibit(?:ed)?)\\b"],
  "forbidden_claims": ["\\b(AW139|EC135|H145)\\b"],
  "threshold": 1,
  "negation_window_tokens": 12,
  "source_docs": ["OM-A", "OM-B", "MEL", "MCM", "OpsSpecs"]
}
```

### Rule Types
- **affirm**: Positive compliance verification
- **deny**: Prohibition verification
- **limit**: Operational limitation verification
- **align_with_opspecs**: Alignment with operational specifications

## 🔧 Troubleshooting

### Common Issues

#### 1. All Rules Show as "MISSING"
**Causes**: Missing dependencies, document files not found, text extraction failures
**Solutions**: 
- Install required packages: `pip install -r requirements.txt`
- Verify all document files are present
- Run debug script to check text extraction

#### 2. Text Extraction Failures
**Causes**: Corrupted files, unsupported formats, permission issues
**Solutions**:
- Verify document integrity
- Check file permissions
- Update Python libraries

#### 3. Pattern Matching Issues
**Causes**: Incorrect patterns, case sensitivity, special characters
**Solutions**:
- Review pattern text carefully
- Use debug script to see extracted text
- Simplify patterns to basic keywords

### Debug Workflow
1. Run debug script: `python debug_text_extraction.py`
2. Check text extraction: Verify documents load correctly
3. Test patterns: See which patterns match/fail
4. Review extracted text: Look for formatting issues
5. Adjust patterns: Modify JSON rules as needed

## 📈 Current Status

### ✅ Completed Features
- Semantic compliance checker with 4-state evaluation
- Document text extraction from multiple formats
- Rule-based compliance checking with semantic patterns
- Evidence collection and confidence scoring
- Excel report generation with detailed analysis
- Project dependency management and setup documentation

### 🔄 In Progress
- Section-aware processing (sectionizer)
- Advanced NLP integration
- Performance optimization

### 📋 Planned Enhancements
- **Sectionizer**: Route rule matching to specific document sections
- **Advanced NLP**: Integration with spaCy for better language understanding
- **Rule Templates**: Standardized patterns for common compliance types
- **Performance Optimization**: Caching and parallel processing
- **Validation Framework**: Automated testing of rule accuracy
- **User Interface**: Web-based interface for non-technical users

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For issues or questions:
1. Check the [COMPLIANCE_CHECKER_DOCUMENTATION.md](COMPLIANCE_CHECKER_DOCUMENTATION.md)
2. Review the [QUICK_REFERENCE_GUIDE.md](QUICK_REFERENCE_GUIDE.md)
3. Run the debug script for troubleshooting
4. Open an issue in the repository

## 🙏 Acknowledgments

- BROOK Aviation for providing the compliance requirements
- Aviation regulatory bodies for establishing compliance standards
- Open source community for the tools and libraries used

---

**Note**: This tool is designed to assist with compliance verification but should not replace professional regulatory review. Always verify results with qualified aviation compliance experts.
