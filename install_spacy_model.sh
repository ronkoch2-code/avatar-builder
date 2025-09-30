#!/bin/bash
# Install spaCy language model
echo "Installing spaCy English language model..."
python3 -m spacy download en_core_web_sm
echo "✓ spaCy model installed"
