# Local Model Integration Guide

## Overview
This guide explains how to use local AI models in the PrepIQ system. All models are installed directly via pip and run locally without requiring external API keys.

## Supported Local Models

### 1. Question Answering
- **Model**: `deepset/roberta-base-squad2` (RoBERTa-based)
- **Capabilities**: Extractive question answering from provided context
- **Performance**: Fast inference on CPU, excellent accuracy

### 2. Text Summarization
- **Model**: `facebook/bart-large-cnn` (BART-based)
- **Capabilities**: Abstractive text summarization
- **Performance**: Good quality summaries, moderate processing time

### 3. Text Classification
- **Model**: `ProsusAI/finbert` (Finance-specific BERT)
- **Capabilities**: Financial sentiment and topic classification
- **Performance**: Specialized for financial text analysis

### 4. Text Generation
- **Model**: `gpt2` (GPT-2 small)
- **Capabilities**: Text continuation and generation
- **Performance**: Fast generation, suitable for short texts

### 5. Sentence Similarity
- **Model**: `all-MiniLM-L6-v2` (Sentence Transformers)
- **Capabilities**: Semantic similarity calculation
- **Performance**: Very fast, excellent for similarity tasks

### 6. Translation
- **Model**: `Helsinki-NLP/opus-mt-en-es` (MarianMT)
- **Capabilities**: English to Spanish translation
- **Performance**: Fast, good quality for common phrases

## Installation

### Automatic Installation
The required models are automatically installed when you install the backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### Manual Installation
If you need to install specific models:

```bash
# Core ML libraries
pip install transformers==4.38.0 torch==2.1.0 sentence-transformers==2.2.2

# Additional utilities
pip install accelerate==0.21.0 tokenizers==0.15.0 datasets==2.16.0
```

## Usage Examples

The local models are automatically used by the ML components. Here's how to use them directly:

```python
from app.ml.external_api_wrapper import external_api

# Question Answering
result = external_api.question_answering(
    context="The Earth orbits the Sun in our solar system",
    question="What orbits the Sun?"
)
print(result["output"])  # "The Earth"

# Text Summarization
result = external_api.text_summarization(
    "Machine learning is a method of data analysis that automates analytical model building. 
     It is a branch of artificial intelligence based on the idea that systems can learn from data, 
     identify patterns and make decisions with minimal human intervention."
)
print(result["output"])  # Concise summary

# Text Classification
result = external_api.text_classification(
    "The company's quarterly earnings exceeded expectations by 15%"
)
print(result["output"])  # {"label": "positive", "score": 0.95}

# Sentence Similarity
result = external_api.sentence_similarity([
    "The cat sat on the mat",
    "A feline rested on the rug"
])
print(result["output"])  # [0.85] (similarity score)
```

## System Requirements

### Minimum Requirements
- **RAM**: 4GB
- **Storage**: 2GB free space
- **Python**: 3.8+
- **OS**: Windows, macOS, or Linux

### Recommended Requirements
- **RAM**: 8GB+ (for better performance)
- **GPU**: CUDA-compatible GPU (optional, for faster processing)
- **Storage**: 5GB+ free space

## Performance Optimization

### GPU Acceleration
If you have a CUDA-compatible GPU:
```bash
# Install CUDA version of PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### CPU Optimization
For CPU-only systems, models will automatically use optimized inference.

### Model Caching
Models are cached locally after first download:
- Location: `~/.cache/huggingface/transformers/`
- Size: ~1-2GB total for all models
- Automatic reuse on subsequent runs

## Fallback Behavior

The system includes intelligent fallback mechanisms:
1. **Primary**: Full models with high accuracy
2. **Fallback**: Lightweight models for basic functionality
3. **Emergency**: Rule-based processing when models fail

## Troubleshooting

### Common Issues

1. **Insufficient Memory**
   - Solution: Close other applications
   - Alternative: Use smaller model variants

2. **Download Failures**
   - Check internet connection
   - Try again (models are cached after successful download)

3. **Slow Performance**
   - Consider GPU acceleration
   - Use smaller models for development

4. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python version compatibility

### Logging
Enable detailed logging for debugging:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Security Notes

- All models run locally - no data leaves your system
- No API keys required
- Models are downloaded from Hugging Face's secure repositories
- Regular updates for security patches

## Model Updates

To update models to newer versions:
```bash
pip install --upgrade transformers sentence-transformers
```

The system will automatically download updated model versions when available.