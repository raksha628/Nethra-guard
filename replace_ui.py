import os
import re

replacements = {
    r"\bDemo Dataset\b": "Analysis Dataset",
    r"\bdemo dataset\b": "analysis dataset",
    r"\bDemo Workspace\b": "Assurance Workspace",
    r"\bdemo workspace\b": "assurance workspace",
    r"\bDemo Model\b": "Registered Model",
    r"\bdemo model\b": "registered model",
    r"\bDemo Run\b": "Assurance Run",
    r"\bdemo run\b": "assurance run",
    r"\bDemo Findings\b": "Assessment Findings",
    r"\bdemo findings\b": "assessment findings",
    r"\bDemo Evidence\b": "Assessment Evidence",
    r"\bdemo evidence\b": "assessment evidence",
    r"\bSynthetic Dataset\b": "Analysis Dataset",
    r"\bsynthetic dataset\b": "analysis dataset",
    r"\bSynthetic Data\b": "Analysis Data",
    r"\bsynthetic data\b": "analysis data",
    r"\bPrototype Mode\b": "Assurance Mode",
    r"\bprototype mode\b": "assurance mode",
    r"\bSample Analysis\b": "Assurance Analysis",
    r"\bsample analysis\b": "assurance analysis",
    r"\bSample Asset\b": "Registered Asset",
    r"\bsample asset\b": "registered asset",
    r"\bMock Data\b": "Analysis Data",
    r"\bmock data\b": "analysis data",
    r"\bTest Dataset\b": "Analysis Dataset",
    r"\btest dataset\b": "analysis dataset",
    r"\bExample Dataset\b": "Analysis Dataset",
    r"\bexample dataset\b": "analysis dataset",
    r"\bSimulated Analysis\b": "Assurance Analysis",
    r"\bsimulated analysis\b": "assurance analysis",
    r"\bDemo Mode\b": "Assurance Mode",
    r"\bdemo mode\b": "assurance mode"
}

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for pattern, repl in replacements.items():
        new_content = re.sub(pattern, repl, new_content)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk('src'):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            replace_in_file(os.path.join(root, file))
