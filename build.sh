#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Pre-download Docling models during build
python -c "from docling.document_converter import DocumentConverter; c = DocumentConverter()"

echo "Build complete."