from pdf.extractor import PDFTextExtractor
from processors.section_segmenter import segment_credit_report
from processors.account_processor import process_accounts
from processors.summary_processor import generate_summary_data
from output.excel_generator import generate_excel_report
from utils.text_splitter import split_by_section_headers
import warnings
import os
from datetime import datetime
import argparse
import json

warnings.filterwarnings("ignore", message="Could get FontBBox from font descriptor*")

def process_credit_report(pdf_file_path):
    """
    Main processing logic for a single credit report PDF.
    Takes a file path, processes it, and returns a JSON object with the full analysis.
    """
    extractor = PDFTextExtractor(pdf_file_path)
    text = extractor.extract_text()
    
    print("\n--- Splitting Document and Processing Chunks ---")
    chunks = split_by_section_headers(text)
    
    final_sections = {
        "report_summary": {},
        "surviving_inquiries": [],
        "accounts": [],
        "credit_repair": []
    }

    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        chunk_sections = segment_credit_report(chunk)
        if chunk_sections and isinstance(chunk_sections, dict):
            final_sections["surviving_inquiries"].extend(chunk_sections.get("surviving_inquiries", []))
            final_sections["accounts"].extend(chunk_sections.get("accounts", []))
            final_sections["credit_repair"].extend(chunk_sections.get("credit_repair", []))
            
            summary_chunk = chunk_sections.get("report_summary")
            if isinstance(summary_chunk, dict):
                final_sections["report_summary"].update(summary_chunk)

    # --- Post-Processing and Data Structuring ---
    all_accounts_raw = final_sections.get("accounts", [])
    reportable_accounts_raw = [
        acc for acc in all_accounts_raw 
        if acc.get("type", "").lower() in ["credit card", "charge account", "revolving"]
    ]
    
    print(f"Found {len(all_accounts_raw)} total accounts. Processing {len(reportable_accounts_raw)} reportable accounts.")
    
    processed_accounts = process_accounts(reportable_accounts_raw)
    inquiries = final_sections.get("surviving_inquiries", [])
    credit_repair_items = final_sections.get("credit_repair", [])

    print("\n--- Generating Financial Summary and AI Analysis ---")
    summary_data = generate_summary_data(
        processed_accounts, 
        inquiries, 
        credit_repair_items, 
        final_sections["report_summary"]
    )

    # --- Assemble the Final JSON Output ---
    ai_analysis_result = summary_data.get("ai_analysis", {})

    final_json_output = {
        "analysis_result": ai_analysis_result,
        "risk_bracket": ai_analysis_result.get("risk_bracket"),
        "analysis_explanation": ai_analysis_result.get("analysis_explanation"),
        "extracted_data": {
            "report_summary": final_sections["report_summary"],
            "processed_reportable_accounts": [acc.to_dict() for acc in processed_accounts],
            "all_accounts_raw": all_accounts_raw,
            "inquiries": inquiries,
            "credit_repair_items": credit_repair_items,
            "payoff_summary": summary_data.get("payoff_summary"),
            "counts": summary_data.get("counts")
        },
        "analysis_completed_at": datetime.now().isoformat()
    }
    
    return final_json_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a credit report PDF and generate a JSON analysis.")
    parser.add_argument("pdf_file", help="The path to the PDF credit report file.")
    args = parser.parse_args()

    # Process the report and get the JSON output
    analysis_json = process_credit_report(args.pdf_file)
    
    # Pretty-print the JSON to the console
    print("\n--- Analysis Complete ---")
    print(json.dumps(analysis_json, indent=4))