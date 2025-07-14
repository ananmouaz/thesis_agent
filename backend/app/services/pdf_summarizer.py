from pathlib import Path
import itertools
import fitz           # PyMuPDF
from transformers import pipeline, AutoTokenizer
import argparse
import textwrap

tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
summarizer = pipeline("summarization",
                      model="facebook/bart-large-cnn",
                      tokenizer=tokenizer)

MAX_INPUT_TOKENS = 900   # keep source chunks <1024


def _token_chunks(text: str, limit: int = MAX_INPUT_TOKENS):
    ids = tokenizer.encode(text, add_special_tokens=False)
    for i in range(0, len(ids), limit):
        yield tokenizer.decode(ids[i:i + limit])


def pdf_to_summary(file_path: str,
                   max_summary_tokens: int = 300,
                   min_summary_tokens: int | None = None,
                   max_chunks: int = 5) -> str:
    """Extract text and return a bullet summary with user-defined length."""
    min_summary_tokens = min_summary_tokens or max(max_summary_tokens // 4, 15)

    doc = fitz.open(file_path)
    full_text = " ".join(p.get_text() for p in doc)

    summaries = [
        summarizer(chunk,
                   max_length=max_summary_tokens,
                   min_length=min_summary_tokens,
                   do_sample=False)[0]["summary_text"]
        for chunk in itertools.islice(_token_chunks(full_text), max_chunks)
    ]
    return "\n• " + "\n• ".join(summaries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Summarise a PDF with adjustable output length."
    )
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--tokens", "-t", type=int, default=300,
                        help="maximum tokens per chunk summary (default: 300)")
    args = parser.parse_args()

    print(textwrap.dedent(pdf_to_summary(args.pdf, max_summary_tokens=args.tokens)))
