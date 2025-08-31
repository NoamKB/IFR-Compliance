# -*- coding: utf-8 -*-
"""
BROOK Compliance Checker — Semantic Upgrade (v0.2)
-------------------------------------------------
This version remains compatible with the simple "contains_any" rules you already used,
but adds **semantic** checks that reduce false-positives and allow "no-approval" detection.

Key additions:
1) Support for more expressive rule fields:
   - rule_type: "affirm" | "deny" | "limit" | "align_with_opspecs"
   - positive_patterns / negative_patterns / forbidden_claims (regex, case-insensitive)
   - threshold (minimal # of positive hits), negation_window_tokens (proximity check)
   - (optional) ops_facts per rule (or a global ops_facts JSON passed via CLI)

2) Decision logic moves from binary FOUND/MISSING to 4-state output:
   - FOUND / MISSING / CONFLICT / REVIEW (still exported under "Result" column)

3) Evidence and confidence:
   - Keeps short snippets from the document as auditable evidence
   - Confidence score is a simple heuristic based on hits and contradictions

4) Backward-compatibility:
   - If a rule only has: {"checks":[{"type":"contains_any","patterns":[...]}]} — it works as before.

NOTE: Section-aware search (the "sectionizer") is NOT implemented here yet.
      In the next step we will add it and route rule matching into anchor_sections.
"""

import json, re, sys
from pathlib import Path
import pandas as pd

# ====== Document mapping (same as original) ======
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

# ====== I/O helpers ======
def load_text_from_doc(path: Path) -> str:
    """
    Load plain text from DOCX/PDF/TXT/MD.
    - For DOCX use python-docx
    - For PDF use PyPDF2 (layout is not preserved but ok for matching)
    - Fail silently and return "" if the file cannot be read
    """
    text = ""
    if not path.exists():
        return ""
    lower = path.suffix.lower()
    try:
        if lower == ".docx":
            from docx import Document
            d = Document(str(path))
            text = "\n".join(p.text for p in d.paragraphs)
        elif lower == ".pdf":
            import PyPDF2
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = []
                for p in reader.pages:
                    try:
                        pages.append(p.extract_text() or "")
                    except Exception:
                        pages.append("")
                text = "\n".join(pages)
        elif lower in [".txt", ".md"]:
            text = path.read_text(encoding="utf-8", errors="ignore")
        else:
            text = ""
    except Exception:
        text = ""
    return text

# Text utilities (used by the semantic matcher) 
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")

def split_sentences(text: str):
    """
    Very naive sentence splitter. Good enough for audit snippets.
    """
    if not text:
        return []
    parts = SENT_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]

def snippet(text: str, start: int, end: int, margin: int = 120) -> str:
    """
    Return a short, auditable snippet around a match.
    """
    a = max(0, start - margin)
    b = min(len(text), end + margin)
    return text[a:b].replace("\\n", " ").strip()

def any_regex(patterns):
    """
    Compile a single regex from a list of regex strings (OR).
    Returns compiled pattern or None if list is empty.
    """
    pats = [p for p in (patterns or []) if p]
    if not pats:
        return None
    return re.compile("(" + "|".join(pats) + ")", re.IGNORECASE | re.MULTILINE | re.DOTALL)

def find_all(pattern, text):
    """
    Yield match objects for a compiled regex pattern over text.
    """
    if not pattern or not text:
        return []
    return list(pattern.finditer(text))

def window_has_negative(text: str, center_span, neg_re, char_window: int) -> bool:
    """
    Check whether any negative pattern appears within +/- char_window chars of a positive match.
    """
    if not neg_re:
        return False
    s, e = center_span
    a = max(0, s - char_window)
    b = min(len(text), e + char_window)
    return bool(neg_re.search(text[a:b]))

#  Core rule evaluation
def evaluate_rule_semantic(rule: dict, doc_text: str, ops_facts: dict | None = None) -> dict:
    """
    Evaluate a rule against given document text.

    Supports fields:
      - rule_type: "affirm" | "deny" | "limit" | "align_with_opspecs" (affects semantics slightly)
      - positive_patterns, negative_patterns, forbidden_claims (regex strings list)
      - threshold (int), negation_window_tokens (int)
      - ops_facts (dict) for certain align checks (e.g., fleet registrations)

    Returns result dict with keys:
      decision: FOUND/MISSING/CONFLICT/REVIEW
      matched_positive: list of snippets
      matched_forbidden: list of snippets
      matched_pattern: first pattern seen (for backward compat column)
      confidence: float in [0,1]
      notes: free text
    """
    # Backward compatibility path: original contains_any
    checks = rule.get("checks", [])
    if checks:
        for chk in checks:
            if chk.get("type") == "contains_any":
                for pat in (chk.get("patterns") or []):
                    if pat and pat.lower() in (doc_text or "").lower():
                        return {
                            "decision": "FOUND",
                            "matched_positive": [],
                            "matched_forbidden": [],
                            "matched_pattern": pat,
                            "confidence": 0.6,
                            "notes": "Legacy contains_any match"
                        }
        return {
            "decision": "MISSING",
            "matched_positive": [],
            "matched_forbidden": [],
            "matched_pattern": "",
            "confidence": 0.0,
            "notes": "Legacy contains_any not found"
        }

    # Semantic path
    rule_type = rule.get("rule_type", "affirm")
    pos_re = any_regex(rule.get("positive_patterns"))
    neg_re = any_regex(rule.get("negative_patterns"))
    forbid_re = any_regex(rule.get("forbidden_claims"))
    threshold = int(rule.get("threshold", 1))
    # Treat tokens window as ~6 chars per token → char window ~ 6 * tokens
    char_window = max(0, int(rule.get("negation_window_tokens", 12)) * 6)

    matched_positive_snips = []
    matched_forbidden_snips = []
    first_pattern = ""

    # 1) Forbidden claims (hard conflict)
    if forbid_re:
        for m in find_all(forbid_re, doc_text):
            matched_forbidden_snips.append(snippet(doc_text, m.start(), m.end()))
    if matched_forbidden_snips and rule_type in {"deny", "limit", "align_with_opspecs", "affirm"}:
        return {
            "decision": "CONFLICT",
            "matched_positive": [],
            "matched_forbidden": matched_forbidden_snips,
            "matched_pattern": first_pattern,
            "confidence": 0.95,
            "notes": "Forbidden claim(s) present"
        }

    # 2) Positive evidence with local negation check
    pos_hits = 0
    if pos_re:
        for m in find_all(pos_re, doc_text):
            if not window_has_negative(doc_text, m.span(), neg_re, char_window):
                pos_hits += 1
                matched_positive_snips.append(snippet(doc_text, m.start(), m.end()))
                if not first_pattern:
                    first_pattern = m.group(0)
            else:
                # local contradiction near a positive — we will downgrade to REVIEW if no clean evidence
                matched_forbidden_snips.append(snippet(doc_text, m.start(), m.end()))

    # 3) Align with ops_facts (simple, generic support for fleet/area)
    notes = []
    if rule_type == "align_with_opspecs" and (ops_facts or rule.get("ops_facts")):
        of = rule.get("ops_facts") or ops_facts or {}
        # a) Fleet registrations present
        regs = of.get("registrations") or []
        if regs:
            missing = [r for r in regs if re.search(re.escape(r), doc_text, re.I) is None]
            if missing:
                notes.append(f"Missing registrations in manuals: {', '.join(missing)}")
        # b) Detect *extra* registrations (simple pattern 4X-XXX that are not in ops_facts)
        if regs:
            all_regs_found = set(re.findall(r"\b[0-9A-Z]{1,2}-[A-Z]{3}\b", doc_text, re.I))
            extras = [r for r in sorted(all_regs_found) if r.upper() not in {x.upper() for x in regs}]
            if extras:
                matched_forbidden_snips.extend([f"Extra reg in manuals: {x}" for x in extras])
        # c) Area (if provided)
        if of.get("area"):
            desired = {a.upper() for a in of["area"]}
            if not any(re.search(re.escape(a), doc_text, re.I) for a in desired):
                notes.append("Area from OpsSpecs not clearly stated in manuals")
        # If we found extras → conflict; if missing → missing (unless other positives compensate)
        if matched_forbidden_snips:
            return {
                "decision": "CONFLICT",
                "matched_positive": matched_positive_snips,
                "matched_forbidden": matched_forbidden_snips,
                "matched_pattern": first_pattern,
                "confidence": 0.9,
                "notes": "; ".join(notes) if notes else "Conflict with ops_facts"
            }
        if notes and pos_hits < threshold:
            return {
                "decision": "MISSING",
                "matched_positive": matched_positive_snips,
                "matched_forbidden": [],
                "matched_pattern": first_pattern,
                "confidence": 0.2,
                "notes": "; ".join(notes)
            }

    # 4) Decide
    if pos_hits >= threshold:
        return {
            "decision": "FOUND",
            "matched_positive": matched_positive_snips,
            "matched_forbidden": [],
            "matched_pattern": first_pattern,
            "confidence": min(1.0, 0.6 + 0.2 * (pos_hits - threshold)),
            "notes": ""
        }
    if matched_positive_snips and matched_forbidden_snips:
        return {
            "decision": "REVIEW",
            "matched_positive": matched_positive_snips,
            "matched_forbidden": matched_forbidden_snips,
            "matched_pattern": first_pattern,
            "confidence": 0.5,
            "notes": "Positive evidence appears near negations/contradictions"
        }
    return {
        "decision": "MISSING",
        "matched_positive": [],
        "matched_forbidden": [],
        "matched_pattern": first_pattern,
        "confidence": 0.0,
        "notes": ""
    }

def main(rules_json_path: str, output_xlsx_path: str, ops_facts_json_path: str | None = None):
    """
    1) Load rules JSON. Accept two shapes:
       - {"rules": [...]} OR just a bare list [...]
    2) Optionally load ops_facts JSON for align_with_opspecs rules.
    3) Load/Cache all mapped documents.
    4) Evaluate each rule and export an Excel file with auditable snippets.
    """
    # ---- Load rules ----
    raw = json.loads(Path(rules_json_path).read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "rules" in raw:
        rules = raw["rules"]
    elif isinstance(raw, list):
        rules = raw
    else:
        raise ValueError("Unsupported rules JSON format")

    # ---- Optional ops_facts ----
    ops_facts = None
    if ops_facts_json_path:
        try:
            ops_facts = json.loads(Path(ops_facts_json_path).read_text(encoding="utf-8"))
        except Exception:
            ops_facts = None

    # ---- Load documents ----
    text_cache = {}
    for key, fname in DOC_FILES.items():
        p = Path(fname)
        text_cache[key] = load_text_from_doc(p)

    # ---- Evaluate rules ----
    results = []
    for r in rules:
        r_id = r.get("id")
        item = r.get("item", "")
        src_docs = r.get("source_docs", ["OpsSpecs"])
        locator = r.get("locator_hint", "")
        owner = r.get("owner", "")
        evidence_hints = "; ".join(r.get("evidence_hints", []))

        # Combine all selected docs (sectionizer to be added later)
        doc_text = "\n".join(text_cache.get(k, "") for k in src_docs)

        # Evaluate using semantic path with fallback to legacy
        outcome = evaluate_rule_semantic(r, doc_text, ops_facts=ops_facts)

        results.append({
            "Rule ID": r_id,
            "Item": item,
            "Source docs": ", ".join(src_docs),
            "Result": outcome["decision"],                               # FOUND / MISSING / CONFLICT / REVIEW
            "Matched pattern (if any)": outcome.get("matched_pattern",""),
            "Evidence (positive)": " | ".join(outcome.get("matched_positive", [])[:3]),
            "Contradiction (if any)": " | ".join(outcome.get("matched_forbidden", [])[:3]),
            "Confidence": round(float(outcome.get("confidence", 0.0)), 2),
            "Locator hint": locator,
            "Owner": owner,
            "Evidence (what to show)": evidence_hints,
            "Notes": outcome.get("notes","")
        })

    # ---- Export ----
    df_cols = [
        "Rule ID","Item","Source docs","Result",
        "Matched pattern (if any)","Evidence (positive)","Contradiction (if any)",
        "Confidence","Locator hint","Owner","Evidence (what to show)","Notes"
    ]
    df = pd.DataFrame(results, columns=df_cols)
    df.to_excel(output_xlsx_path, index=False)

if __name__ == "__main__":
    # CLI:
    #   python run_compliance_check_semantic.py rules.json out.xlsx [ops_facts.json]
    rules_json = sys.argv[1] if len(sys.argv) > 1 else "brook_rules_from_spec.json"
    out_xlsx = sys.argv[2] if len(sys.argv) > 2 else "brook_compliance_report.xlsx"
    ops_facts_json = sys.argv[3] if len(sys.argv) > 3 else None
    main(rules_json, out_xlsx, ops_facts_json)
