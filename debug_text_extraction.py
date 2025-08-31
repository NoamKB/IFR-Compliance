#!/usr/bin/env python3
"""
Debug script to test text extraction and pattern matching
"""

import json
from pathlib import Path
from docx import Document
import PyPDF2

def load_text_from_doc(path: Path) -> str:
    """Load text from document with better error handling"""
    text = ""
    if not path.exists():
        print(f"File not found: {path}")
        return ""
    
    lower = path.suffix.lower()
    try:
        if lower == ".docx":
            print(f"Loading DOCX: {path}")
            d = Document(str(path))
            paragraphs = []
            for i, p in enumerate(d.paragraphs):
                if p.text.strip():
                    paragraphs.append(p.text.strip())
                    if len(paragraphs) <= 5:  # Show first 5 non-empty paragraphs
                        print(f"  Para {i}: {p.text[:100]}")
            text = "\n".join(paragraphs)
            print(f"  Total non-empty paragraphs: {len(paragraphs)}")
            
        elif lower == ".pdf":
            print(f"Loading PDF: {path}")
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = []
                for i, p in enumerate(reader.pages):
                    try:
                        page_text = p.extract_text() or ""
                        if page_text.strip():
                            pages.append(page_text.strip())
                            if len(pages) <= 3:  # Show first 3 non-empty pages
                                print(f"  Page {i}: {page_text[:100]}")
                    except Exception as e:
                        print(f"  Error extracting page {i}: {e}")
                        pages.append("")
                text = "\n".join(pages)
                print(f"  Total non-empty pages: {len(pages)}")
                
        else:
            print(f"Unsupported file type: {lower}")
            text = ""
            
    except Exception as e:
        print(f"Error loading {path}: {e}")
        text = ""
    
    return text

def test_pattern_matching(doc_text: str, patterns: list, rule_name: str):
    """Test pattern matching for a specific rule"""
    print(f"\n--- Testing Rule: {rule_name} ---")
    print(f"Document text length: {len(doc_text)}")
    print(f"First 200 chars: {repr(doc_text[:200])}")
    
    found_patterns = []
    for pattern in patterns:
        if pattern and pattern.lower() in doc_text.lower():
            found_patterns.append(pattern)
            print(f"  ✓ Found pattern: {pattern}")
        else:
            print(f"  ✗ Missing pattern: {pattern}")
    
    print(f"Found {len(found_patterns)} out of {len(patterns)} patterns")
    return len(found_patterns) > 0

def main():
    # Load rules
    rules_file = "brook_rules_from_spec_patched.json"
    if not Path(rules_file).exists():
        print(f"Rules file not found: {rules_file}")
        return
    
    with open(rules_file, 'r', encoding='utf-8') as f:
        rules_data = json.load(f)
    
    rules = rules_data.get("rules", [])
    print(f"Loaded {len(rules)} rules")
    
    # Test first few rules
    for i, rule in enumerate(rules[:3]):  # Test first 3 rules
        rule_id = rule.get("id", f"rule_{i}")
        item = rule.get("item", "Unknown")
        source_docs = rule.get("source_docs", [])
        checks = rule.get("checks", [])
        
        print(f"\n{'='*60}")
        print(f"Rule {i+1}: {rule_id}")
        print(f"Item: {item}")
        print(f"Source docs: {source_docs}")
        
        # Load text from source documents
        doc_texts = {}
        for doc_key in source_docs:
            doc_file = None
            if doc_key == "OpsSpecs":
                doc_file = "Opspecs Brook BHSBEXBHT -BOB - 27-04-2025.pdf"
            elif doc_key == "AOC":
                doc_file = "AOC 23-24.pdf"
            elif doc_key == "OM-A":
                doc_file = "OMA - REV 05.docx"
            elif doc_key == "OM-B":
                doc_file = "OMB - REV 05.docx"
            elif doc_key == "OM-C":
                doc_file = "OMC  - REV 05.docx"
            elif doc_key == "OM-D":
                doc_file = "OMD - REV 05.docx"
            elif doc_key == "MEL":
                doc_file = "BROOK S-76 MEL 4X-BHS,BHP,BHT,BEX,BOB,BOA, BOI S76C++ Rev 6 (1 Aug 2025).docx"
            elif doc_key == "MCM":
                doc_file = "BROOK MCM REV 4 - 1 Aug 2025.docx"
            elif doc_key == "SMS":
                doc_file = "mod_Brook SMS Manual rev 0.docx"
            elif doc_key == "ERP":
                doc_file = "ERP Draft - Final (1) (1).docx"
            
            if doc_file and Path(doc_file).exists():
                doc_texts[doc_key] = load_text_from_doc(Path(doc_file))
            else:
                print(f"  Document file not found: {doc_file}")
                doc_texts[doc_key] = ""
        
        # Test pattern matching
        combined_text = "\n".join(doc_texts.values())
        for check in checks:
            check_type = check.get("type")
            patterns = check.get("patterns", [])
            
            if check_type == "contains_any":
                found = test_pattern_matching(combined_text, patterns, f"{rule_id} - {check_type}")
                print(f"  Overall result: {'FOUND' if found else 'MISSING'}")

if __name__ == "__main__":
    main()

