# Bytez API Setup Guide

## Overview

PrepIQ now uses **Bytez API** for all ML model inference, eliminating the need for local PyTorch installation and avoiding DLL errors on Windows.

## Setup Instructions

### 1. Install Bytez SDK

```powershell
pip install bytez
```

### 2. Set Your Bytez API Key

Add your Bytez API key to your `.env` file:

```env
BYTEZ_API_KEY=d02578a68c2621c9fdac702219d0722e
```

If no API key is provided, the system will use the default key from the code.

### 3. Restart the Backend

```powershell
python backend\start_server.py
```

## Models Available via Bytez

All 8 models are now powered by Bytez API:

1. **Question Answering** - `deepset/roberta-base-squad2`
2. **Text Summarization** - `facebook/bart-large-cnn`
3. **Text Classification** - `ProsusAI/finbert`
4. **Text Generation** - `gpt2`
5. **Sentence Similarity** - `sentence-transformers/all-MiniLM-L6-v2`
6. **Translation** - `Helsinki-NLP/opus-mt-en-es`
7. **Image Captioning** - `Salesforce/blip-image-captioning-large`
8. **Chat/Conversation** - `microsoft/DialoGPT-medium`

## Benefits

✅ **No PyTorch DLL errors** - All inference happens on Bytez servers  
✅ **No local model downloads** - Models are hosted remotely  
✅ **Faster startup** - No need to load large models locally  
✅ **Better performance** - Bytez handles GPU acceleration  
✅ **Easy updates** - Switch models without reinstalling dependencies  

## Fallback Behavior

If Bytez API is unavailable, the system will automatically use lightweight fallback methods:
- Basic keyword matching for QA
- Sentence extraction for summarization
- Word overlap for similarity
- Simple text processing for other tasks

## Testing Models

You can test all models are working by checking the server logs. You should see:

```
Bytez SDK initialized successfully
Bytez API wrapper initialized successfully - all models available via Bytez
Loaded Bytez model: deepset/roberta-base-squad2 for qa
Loaded Bytez model: facebook/bart-large-cnn for summarization
...
```

## Troubleshooting

### Bytez SDK Not Found
```powershell
pip install bytez
```

### API Key Issues
- Check your `.env` file has `BYTEZ_API_KEY` set
- Verify your API key is valid at https://bytez.com

### Model Loading Errors
- Models are loaded lazily (on first use)
- Check server logs for specific model errors
- Fallback methods will be used automatically

## Model Customization

To use different Bytez models, edit `backend/app/ml/external_api_wrapper.py` and update the `model_mappings` dictionary:

```python
self.model_mappings = {
    'qa': 'your-model-name',
    'summarization': 'your-model-name',
    # ... etc
}
```
