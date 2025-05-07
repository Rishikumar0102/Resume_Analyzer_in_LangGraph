# 📄 AI Resume Analysis Tool

**A smart resume analyzer that compares resumes against job descriptions using AI (Groq/Llama3) to generate match scores, skill gaps, and actionable feedback.**

---

## 🌟 Key Features

- **PDF Text Extraction**: Accurate parsing of resume content using PyMuPDF
- **AI-Powered Analysis**: LLM-driven comparison with Groq's Llama3-8b
- **Skills Matching**: 
  - ✅ Identifies matching skills (Python, AWS, etc.)
  - ❌ Highlights missing requirements
- **Scoring System**:
  - Suitability score (0-100)
  - Color-coded feedback (Green/Orange/Red)
- **Actionable Insights**:
  - Strengths list
  - Improvement suggestions
- **Secure Processing**: Local text processing (no resume data stored)

---

## 🛠️ Tech Stack

| Component          | Technology Used          |
|--------------------|--------------------------|
| Backend Framework  | Flask (Python)           |
| PDF Processing     | PyMuPDF (fitz)           |
| AI Engine          | Groq API + Llama3-8b     |
| Frontend           | HTML5 + Jinja2 Templates |
| Text Processing    | Regex + Custom Parsers   |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- [Groq API Key](https://console.groq.com/keys) (Free tier available)
- Pip package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/resume-analyzer.git
   cd resume-analyzer