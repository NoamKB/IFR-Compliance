#!/usr/bin/env python3
"""
Analyze the compliance report
"""

import pandas as pd

def main():
    # Read the report
    df = pd.read_excel('brook_compliance_report_semantic.xlsx')
    
    print("Compliance Report Summary")
    print("=" * 50)
    print(f"Total Rules: {len(df)}")
    print(f"Found: {len(df[df['Result'] == 'FOUND'])}")
    print(f"Missing: {len(df[df['Result'] == 'MISSING'])}")
    
    print("\nDetailed Results:")
    print("-" * 50)
    for _, row in df.iterrows():
        print(f"{row['Rule ID']}: {row['Result']}")
    
    print("\nMissing Rules (if any):")
    print("-" * 50)
    missing = df[df['Result'] == 'MISSING']
    if len(missing) > 0:
        for _, row in missing.iterrows():
            print(f"{row['Rule ID']}: {row['Item']}")
    else:
        print("No missing rules found!")

if __name__ == "__main__":
    main()

