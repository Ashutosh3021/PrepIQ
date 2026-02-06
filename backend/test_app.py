import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    from app.main import app
    print("✓ FastAPI app imported successfully")
    
    # Print available routes
    print("\nAvailable routes:")
    for route in app.routes:
        if hasattr(route, 'methods'):
            for method in route.methods:
                print(f"  {method} {route.path}")
        else:
            print(f"  GET {route.path}")
    
    print("\nLooking for auth routes specifically:")
    auth_routes = [route for route in app.routes if hasattr(route, 'path') and '/auth' in route.path]
    for route in auth_routes:
        if hasattr(route, 'methods'):
            for method in route.methods:
                print(f"  ✓ {method} {route.path}")
        else:
            print(f"  ✓ GET {route.path}")
            
    print("\nApp is ready!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()