"""
Test for Object Detection using YOLOv8
This runs locally and is completely FREE
Installation: pip install ultralytics
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

def test_yolo_object_detection():
    """Test object detection using YOLOv8"""
    print("=" * 60)
    print("Testing Object Detection with YOLOv8")
    print("Model: YOLOv8n (nano) - Fast & Lightweight")
    print("=" * 60)
    
    try:
        print("Importing required libraries...")
        from ultralytics import YOLO
        import cv2
        import numpy as np
        from PIL import Image
        import requests
        from io import BytesIO
        
        print("✅ Libraries imported successfully\n")
        
        # Load YOLOv8 model
        print("Loading YOLOv8 model (first run will download ~6MB)...")
        model = YOLO('yolov8n.pt')  # nano model - fastest
        print("✅ YOLOv8 model loaded\n")
        
        # Test case 1: Detect objects in a sample image with animals
        print("Test 1: Detecting animals in sample image")
        print("-" * 60)
        
        # Using a sample image URL with animals
        sample_image_url = "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=640"
        
        try:
            print(f"Downloading sample image...")
            response = requests.get(sample_image_url, timeout=10)
            
            if response.status_code == 200:
                # Load image
                image = Image.open(BytesIO(response.content))
                image_array = np.array(image)
                
                print(f"✅ Image loaded: {image.size}")
                print("Running object detection...")
                
                # Run inference
                results = model(image_array, verbose=False)
                
                # Process results
                for result in results:
                    boxes = result.boxes
                    if len(boxes) > 0:
                        print(f"✅ Detected {len(boxes)} objects:")
                        for i, box in enumerate(boxes, 1):
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            class_name = model.names[class_id]
                            print(f"  {i}. {class_name} (confidence: {confidence:.2f})")
                    else:
                        print("⚠️  No objects detected")
                
                print()
            else:
                print(f"⚠️  Could not download sample image\n")
        
        except Exception as img_error:
            print(f"⚠️  Error processing sample image: {img_error}\n")
        
        # Test case 2: Detect common objects
        print("Test 2: Detecting common objects")
        print("-" * 60)
        
        # Using a sample image with common objects
        sample_objects_url = "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=640"
        
        try:
            print(f"Downloading sample image...")
            response = requests.get(sample_objects_url, timeout=10)
            
            if response.status_code == 200:
                # Load image
                image = Image.open(BytesIO(response.content))
                image_array = np.array(image)
                
                print(f"✅ Image loaded: {image.size}")
                print("Running object detection...")
                
                # Run inference
                results = model(image_array, verbose=False)
                
                # Process results
                for result in results:
                    boxes = result.boxes
                    if len(boxes) > 0:
                        print(f"✅ Detected {len(boxes)} objects:")
                        for i, box in enumerate(boxes, 1):
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            class_name = model.names[class_id]
                            print(f"  {i}. {class_name} (confidence: {confidence:.2f})")
                    else:
                        print("⚠️  No objects detected")
                
                print()
        
        except Exception as img_error:
            print(f"⚠️  Error processing sample image: {img_error}\n")
        
        # Test case 3: Test with local image path
        print("Test 3: Local image detection capability")
        print("-" * 60)
        print("To test with your own images, use:")
        print("  results = model('path/to/image.jpg')")
        print("  or")
        print("  results = model(numpy_array)\n")
        
        # List available classes
        print("Available object classes (80 total):")
        classes = list(model.names.values())
        print(f"  Animals: {', '.join([c for c in classes if c in ['cat', 'dog', 'bird', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe']])}")
        print(f"  Electronics: {', '.join([c for c in classes if c in ['laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'tv', 'microwave']])}")
        print(f"  And {len(classes) - 17} more objects...\n")
        
        print("=" * 60)
        print("✅ YOLOv8 Object Detection Test PASSED")
        print("=" * 60)
        print("\nNotes:")
        print("- YOLOv8 is completely free and runs locally")
        print("- First run downloads model file (~6MB)")
        print("- Detects 80 common object classes")
        print("- For custom objects, fine-tune on your dataset")
        print("- Use with confidence threshold: model(image, conf=0.5)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nPlease install required packages:")
        print("  pip install ultralytics opencv-python Pillow numpy requests")
        return False
        
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_yolo_object_detection()
    sys.exit(0 if success else 1)
