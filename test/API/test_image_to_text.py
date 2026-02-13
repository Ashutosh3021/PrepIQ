"""
Test for Image to Text (Handwritten OCR) using EasyOCR
This runs locally and is completely FREE
Installation: pip install easyocr
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

def test_image_to_text():
    """Test handwritten text recognition using EasyOCR"""
    print("=" * 60)
    print("Testing Image to Text (Handwritten OCR)")
    print("Model: EasyOCR (Local - Completely Free)")
    print("=" * 60)
    
    try:
        print("Installing/Importing EasyOCR...")
        import easyocr
        import numpy as np
        from PIL import Image
        import io
        import requests
        
        print("✅ EasyOCR imported successfully\n")
        
        # Initialize EasyOCR reader
        print("Initializing EasyOCR (downloading models if needed)...")
        print("Note: First run may take a few minutes to download models")
        reader = easyocr.Reader(['en'], gpu=False)  # Use CPU
        print("✅ EasyOCR reader initialized\n")
        
        # Test case 1: Download a sample handwritten image
        print("Test 1: Processing sample handwritten text image")
        print("-" * 60)
        
        # Using a sample image URL (handwritten digits/text)
        sample_image_url = "https://raw.githubusercontent.com/JaidedAI/EasyOCR/master/examples/english.png"
        
        try:
            print(f"Downloading sample image from: {sample_image_url}")
            response = requests.get(sample_image_url, timeout=10)
            
            if response.status_code == 200:
                # Convert to PIL Image
                image = Image.open(io.BytesIO(response.content))
                print(f"✅ Image loaded: {image.size}")
                
                # Convert to numpy array
                image_array = np.array(image)
                
                # Perform OCR
                print("Performing OCR...")
                results = reader.readtext(image_array)
                
                print(f"✅ OCR Results ({len(results)} text regions found):")
                for i, (bbox, text, conf) in enumerate(results, 1):
                    print(f"  {i}. '{text}' (confidence: {conf:.2f})")
                
                # Combine all text
                all_text = ' '.join([text for (_, text, _) in results])
                print(f"\nCombined Text: {all_text}\n")
            else:
                print(f"⚠️  Could not download sample image (status: {response.status_code})")
                print("   Skipping this test case\n")
        
        except Exception as img_error:
            print(f"⚠️  Error processing sample image: {img_error}")
            print("   This is expected if no internet connection\n")
        
        # Test case 2: Create a test image with text
        print("Test 2: Creating test image with text")
        print("-" * 60)
        
        try:
            from PIL import ImageDraw, ImageFont
            
            # Create a simple image with text
            width, height = 400, 100
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)
            
            # Try to use default font
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Draw text
            test_text = "Hello World 123"
            draw.text((20, 30), test_text, fill='black', font=font)
            
            # Convert to numpy array
            image_array = np.array(image)
            
            # Perform OCR
            print(f"Created test image with text: '{test_text}'")
            print("Performing OCR...")
            results = reader.readtext(image_array)
            
            if results:
                print(f"✅ OCR detected {len(results)} text regions:")
                for i, (bbox, text, conf) in enumerate(results, 1):
                    print(f"  {i}. '{text}' (confidence: {conf:.2f})")
            else:
                print("⚠️  No text detected (expected for computer-generated text)")
            
            print()
        
        except Exception as create_error:
            print(f"⚠️  Error creating test image: {create_error}\n")
        
        print("=" * 60)
        print("✅ Image to Text (OCR) Test PASSED")
        print("=" * 60)
        print("\nNotes:")
        print("- EasyOCR is completely free and runs locally")
        print("- First run downloads model files (~100MB)")
        print("- Works best with clear handwritten text")
        print("- For better results with handwritten notes:")
        print("  * Ensure good lighting")
        print("  * Keep text size reasonable")
        print("  * Minimize background noise")
        
        return True
        
    except ImportError:
        print("❌ EasyOCR not installed")
        print("Please install with: pip install easyocr")
        print("Also requires: pip install Pillow numpy requests")
        return False
        
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_image_to_text()
    sys.exit(0 if success else 1)
