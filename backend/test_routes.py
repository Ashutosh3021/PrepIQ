import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import app
    print("=== Available Routes ===")
    for route in app.routes:
        if hasattr(route, 'methods'):
            for method in route.methods:
                print(f"{method} {route.path}")
        else:
            print(f"GET {route.path}")
    
    print("\n=== Auth Routes ===")
    auth_routes = [route for route in app.routes if hasattr(route, 'path') and '/auth' in route.path]
    for route in auth_routes:
        if hasattr(route, 'methods'):
            for method in route.methods:
                print(f"  {method} {route.path}")
        else:
            print(f"  GET {route.path}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()