# PDF Text Analyzer

A FastAPI-based web application for analyzing Korean PDF documents. The system extracts text from PDFs and provides visualization options including word clouds and frequency analysis.

## Features

- PDF text extraction
- Word cloud generation
- Word frequency analysis with visualization
- Customizable stopwords handling
- Real-time analysis via web interface

## Prerequisites

- Python 3.7+
- Korean language support
- Windows: Malgun Gothic font
- macOS: AppleGothic font
- Linux: NanumGothic font

## Installation

```bash
pip install fastapi pdfplumber wordcloud matplotlib konlpy
```

## Configuration

Create an upload directory:
```bash
mkdir upload
```

## Usage

1. Start the server:
```bash
uvicorn main:app --reload
```

2. Access the web interface at `http://localhost:8000`

3. Upload a PDF file and choose analysis type:
   - Wordcloud: Visual representation of word frequency
   - Frequency Analysis: Bar chart of top 10 most frequent words

## Customization

Default stopwords can be modified in the `get_default_stopwords()` function. The system uses KoNLPy's Okt morphological analyzer for Korean text processing.


## Notes

- The system automatically cleans up the upload directory on shutdown
- Supports Korean text extraction and processing
- Includes debug logging for troubleshooting