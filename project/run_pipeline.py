# === Imports ===
import os
import json
import datetime
from pathlib import Path
import fitz  # PyMuPDF
import re
import argparse
from sentence_transformers import SentenceTransformer, util

# === Load Offline Model ===
local_model_path = Path(__file__).resolve().parent.parent / "models" / "all-MiniLM-L6-v2"
sentence_model = SentenceTransformer(str(local_model_path))


# === Argument Parser ===
parser = argparse.ArgumentParser()
parser.add_argument("--pdf_dir", type=str, required=True)
parser.add_argument("--outline_dir", type=str, required=True)
parser.add_argument("--output_dir", type=str, required=True)
parser.add_argument("--input_json", type=str, required=True)
args = parser.parse_args()

PDF_DIR = Path(args.pdf_dir)
OUTLINE_DIR = Path(args.outline_dir)
OUTPUT_DIR = Path(args.output_dir)
INPUT_JSON = Path(args.input_json)

# === Utility Functions ===

def get_line_text(line):
    text = " ".join(span["text"] for span in line.get("spans", [])).strip()
    return re.sub(r"\s+", " ", text)

def classify_heading(line):
    text = get_line_text(line)
    if not text or text.lower() in {"overview", "acknowledgements", "introduction", "conclusion"}:
        return None
    if re.match(r"^\d+\.\d+\.\d+\s", text): return "H3"
    elif re.match(r"^\d+\.\d+\s", text): return "H2"
    elif re.match(r"^\d+\.\s", text): return "H1"
    spans = line.get("spans", [])
    sizes = [s.get("size", 0) for s in spans]
    flags = [s.get("flags", 0) for s in spans]
    max_size = max(sizes, default=0)
    is_bold = any(f & 2 for f in flags)
    if max_size > 18 and is_bold: return "H1"
    elif max_size > 14: return "H2"
    elif max_size > 11: return "H3"
    return None

def extract_outline(pdf_path):
    doc = fitz.open(pdf_path)
    outline = []
    seen = set()
    title = pdf_path.stem
    for i, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                level = classify_heading(line)
                text = get_line_text(line)
                if level and text not in seen and len(text.split()) > 1:
                    seen.add(text)
                    outline.append({"level": level, "text": text, "page": i + 1})
    first_h1 = next((item["text"] for item in outline if item["level"] == "H1"), None)
    return {"title": first_h1 or title, "outline": outline}

def generate_all_outlines(input_data):
    OUTLINE_DIR.mkdir(exist_ok=True)
    for doc in input_data["documents"]:
        pdf_path = PDF_DIR / doc["filename"]
        outline_path = OUTLINE_DIR / f"{pdf_path.stem}.json"
        if outline_path.exists(): continue
        try:
            result = extract_outline(pdf_path)
            with open(outline_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"✅ Outline created: {outline_path.name}")
        except Exception as e:
            print(f"❌ Failed to process {pdf_path.name}: {e}")

def extract_text_under_heading(pdf_path, heading_text, page_number):
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_number - 1)
        blocks = page.get_text("blocks")
        found_heading = False
        content = []
        for block in blocks:
            block_text = block[4].strip()
            if not found_heading:
                if heading_text.lower() in block_text.lower():
                    found_heading = True
            else:
                if len(block_text.split()) < 3 or re.match(r"^\d+(\.\d+)*\s", block_text):
                    break
                content.append(block_text)
        return " ".join(content).strip()
    except Exception as e:
        print(f"⚠️ Failed to extract text for {heading_text} in {pdf_path.name}: {e}")
        return ""

def rank_sections_by_prompt(outlines, prompt_text, max_sections=2):
    prompt_emb = sentence_model.encode(prompt_text, convert_to_tensor=True)
    scored = []
    for entry in outlines:
        section_text = entry["text"]
        if len(section_text.split()) < 3 or section_text.lower() in {"overview", "conclusion"}:
            continue
        section_emb = sentence_model.encode(section_text, convert_to_tensor=True)
        score = util.cos_sim(prompt_emb, section_emb).item()
        scored.append({**entry, "score": score})
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:max_sections]

def build_final_output(input_json, outline_by_doc):
    timestamp = datetime.datetime.utcnow().isoformat()
    persona = input_json["persona"]["role"]
    task = input_json["job_to_be_done"]["task"]

    prompt = f"You are a {persona}. Your goal is to {task}. Find sections that help you accomplish this goal."

    metadata = {
        "input_documents": [doc["filename"] for doc in input_json["documents"]],
        "persona": persona,
        "job_to_be_done": task,
        "processing_timestamp": timestamp
    }

    extracted_sections = []
    subsection_analysis = []
    rank = 1

    for doc_name, outline in outline_by_doc.items():
        top_sections = rank_sections_by_prompt(outline, prompt, max_sections=2)
        for sec in top_sections:
            extracted_sections.append({
                "document": doc_name,
                "section_title": sec["text"],
                "importance_rank": rank,
                "page_number": sec["page"]
            })
            refined = extract_text_under_heading(PDF_DIR / doc_name, sec["text"], sec["page"])
            subsection_analysis.append({
                "document": doc_name,
                "refined_text": refined or sec["text"],
                "page_number": sec["page"]
            })
            rank += 1

    return {
        "metadata": metadata,
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

def run_pipeline():
    if not INPUT_JSON.exists():
        print("❌ input.json not found.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    generate_all_outlines(input_data)

    outline_by_doc = {}
    for doc in input_data["documents"]:
        outline_path = OUTLINE_DIR / f"{Path(doc['filename']).stem}.json"
        if outline_path.exists():
            with open(outline_path, "r", encoding="utf-8") as f:
                outline_by_doc[doc["filename"]] = json.load(f)["outline"]
        else:
            print(f"⚠️ Missing outline for: {doc['filename']}")

    result = build_final_output(input_data, outline_by_doc)
    out_path = OUTPUT_DIR / "final_output.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ Final output written: {out_path}")

if __name__ == "__main__":
    run_pipeline()
