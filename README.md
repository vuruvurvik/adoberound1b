# 📄 Adobe India Hackathon 2025 - Offline Document Understanding Pipeline

## 📌 Project Objective

This project provides an **offline semantic document parsing solution** that:
- Extracts structured outlines from multiple PDFs
- Understands a user-defined persona and task
- Ranks and retrieves the most relevant content sections
- Outputs a structured JSON summary — without any internet dependency

---

## 📂 Folder Structure

```
adoberound1b/
│
├── models/
│   └── all-MiniLM-L6-v2/           ← Local sentence transformer model (offline)
│       ├── pytorch_model.bin
│       ├── config.json
│       ├── tokenizer.json
│       └── ... (other model files)
│
└── project/
    ├── pdfs/                       ← Input PDFs
    ├── outlines/                   ← Auto-generated outlines from PDFs
    ├── outputs/                    ← Final output (JSON)
    ├── input.json                  ← Input config with persona & task
    ├── run_pipeline.py             ← Main processing script
    └── model.py                    ← (optional utility/helper file)
```

---

## 🧠 Core Features

- 📎 Extracts document outlines using visual PDF structure
- 🧠 Semantic similarity ranking with an offline model
- 🔍 Retrieves relevant sections based on a user’s **persona** and **task**
- 🧾 Fully offline pipeline — no web/API/model download needed

---

## 📥 How to Install

Create your virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install sentence-transformers==2.2.2
pip install PyMuPDF
```

> ✅ No Hugging Face downloads needed — the model is already present in `/models/all-MiniLM-L6-v2/`

---

## 📝 `input.json` Format

This file drives the prompt generation and relevance search.

```json
{
  "persona": {
    "role": "Travel Planner"
  },
  "job_to_be_done": {
    "task": "Plan a trip of 4 days for a group of 10 college friends."
  },
  "documents": [
    { "filename": "South of France - Cities.pdf" },
    { "filename": "South of France - Cuisine.pdf" }
  ]
}
```

You can update the persona/task and include more PDFs for analysis.

---

## ▶️ How to Run

```bash
python project/run_pipeline.py   --pdf_dir "project/pdfs"   --outline_dir "project/outlines"   --output_dir "project/outputs"   --input_json "project/input.json"
```

This will generate `final_output.json` inside `project/outputs/`.

---

## 📤 Output Format

Example structure of the output:

```json
{
  "metadata": {
    "input_documents": ["South of France - Cities.pdf"],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a trip of 4 days for a group of 10 college friends.",
    "processing_timestamp": "..."
  },
  "extracted_sections": [
    {
      "document": "...",
      "section_title": "...",
      "importance_rank": 1,
      "page_number": 5
    }
  ],
  "subsection_analysis": [
    {
      "document": "...",
      "refined_text": "...",
      "page_number": 5
    }
  ]
}
```

---

## ❌ Internet Independence

This solution is designed to work **100% offline**:

- ✅ SentenceTransformer model is loaded from `models/` directory
- ✅ No API keys or network calls are made
- ✅ Can be used in secure/air-gapped environments

---

## 🛠️ Tech Stack

- Python 3.10+
- [`PyMuPDF`](https://pymupdf.readthedocs.io/)
- [`sentence-transformers`](https://www.sbert.net/)
- No external model downloads or inference APIs

---

## 📦 What's Included

- 🔹 PDF input files (in `pdfs/`)
- 🔹 Offline pre-trained model (`models/`)
- 🔹 Complete runnable pipeline script
- 🔹 Output + outline folders
- 🔹 This `README.md`
- 🔹 Sample `input.json`

---

## 📄 License

MIT License or as governed by Adobe India Hackathon terms.

---

## 🤝 Authors

- Neural Ninjas(Vasavi College of Engineering,Hyderabad)
  Team members:
  P.Pardiv Sai Charan
- Adobe India Hackathon 2025