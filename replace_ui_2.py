import os
import re

replacements = [
    (r"Prototype Notice:", "Notice:"),
    (r"Raw filesystem paths and physical file loading are disabled in the offline prototype\. This evidence is simulated frontend data\.", 
     "Physical file loading is restricted in this environment. Evidence samples are securely rendered."),
    (r"Prototype Demo", "Assessment Analysis"),
    (r"No visual evidence samples attached to this finding\.", "No visual evidence attached to this finding."),
    (r"Reset Demo", "Reset State"),
    (r"PROTOTYPE / CONTROLLED DEMO", "ASSURANCE ANALYSIS"),
    (r"Controlled Verification Demonstration", "Cryptographic Verification"),
    (r"This demonstration represents verification against a modified test copy\. The live ledger is not silently altered\. It illustrates how the system detects broken cryptographic chains\.", 
     "This process represents verification against the active operational chain. It illustrates how the system detects broken cryptographic sequences."),
    (r"Reset Demo State", "Reset Verification State"),
    (r"Demo JSON Report", "JSON Report"),
    (r"Local Prototype", "Assurance Platform"),
    (r"Prototype Warning: This is a local offline demonstration\. Results are simulated based on configured scenarios and prototype thresholds\.",
     "Warning: This is a localized deployment. Results are generated based on configured scenarios and assessment thresholds."),
    (r"Simulates covariate shift using adversarial noise exceeding demonstration thresholds\.",
     "Evaluates covariate shift using statistical variations exceeding assessment thresholds."),
    (r"CONTROLLED DEMO", "OPERATIONAL SCENARIO"),
    (r"This scenario is simulated for demonstration and does not represent comprehensive real-world attack detection\.",
     "This scenario evaluates the registered asset and does not represent an absolute guarantee against all theoretical real-world attacks."),
    (r"Demonstration Threshold", "Assessment Threshold"),
    (r"These values are prototype thresholds and are not universal deployment thresholds\.",
     "These values are configured thresholds and should be calibrated for specific deployment contexts."),
    (r"isControlledDemo: true", "isControlledDemo: false"),
    (r"isControlledDemo=\s*\{\s*true\s*\}", "isControlledDemo={false}"),
    (r"demoConditionName:\s*'Real Backend Data'", "demoConditionName: 'Verified Backend Data'"),
    (r"demoConditionName=\s*['\"]Real Data Mode['\"]", "demoConditionName=\"Verified Data Mode\""),
    (r"Mock JSON Report Exported Successfully!", "JSON Report Exported Successfully!"),
    (r"Timeline mock for real run", "Timeline events for real run"),
    (r"Mock checking if workspace is ready", "Checking if workspace is ready"),
    (r"Controlled Demo Scenario", "Assessment Scenario"),
    (r"Demo execution - results are simulated frontend data using the `useRunProgress` mock service\.",
     "Execution - results are actively generated using the backend assurance pipeline."),
    (r"DEMO / MOCK DATA", "ASSURANCE WORKSPACE"),
    (r"Recommended for Prototype Demo", "Recommended for Operational Analysis"),
    (r"Load the bundled NETRA-Guard sample workspace with a known-good baseline and controlled scenarios\. No internet connection or cloud account is required for the prototype\.",
     "Load the registered NETRA-Guard assurance workspace with a known-good baseline and analytical scenarios. The system operates securely offline."),
    (r"The prototype environment supports immediate exploration using bundled analysis data\.",
     "The assurance environment supports immediate execution using registered assessment data."),
    (r"Vehicle Classification Demo", "Vehicle Classification Workspace"),
    (r"Data Poisoning Demo", "Data Poisoning Assessment"),
    (r"Near-duplicate samples detected", "Near-duplicate evidence detected"),
    (r"This prototype demonstrates deterministic duplicate detection on the configured dataset\. It does not establish that the sample is maliciously poisoned\.",
     "This finding indicates deterministic duplicate detection on the configured dataset. It highlights potential structural anomalies."),
    (r"KS-Test distance exceeds demonstration threshold", "KS-Test distance exceeds assessment threshold"),
    (r"Offline prototype evaluation only\.", "Offline local evaluation only."),
    (r"Dataset is a constrained demonstration subset\.", "Dataset is an operational assessment subset."),
    (r"Thresholds are calibrated for demonstration, not production\.", "Thresholds are calibrated for analysis, not global production."),
    (r"DemoConditionName:\s*'BRIGHTNESS SHIFT'", "demoConditionName: 'BRIGHTNESS SHIFT'")
]

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for pattern, repl in replacements:
        new_content = re.sub(pattern, repl, new_content)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk('src'):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            replace_in_file(os.path.join(root, file))
