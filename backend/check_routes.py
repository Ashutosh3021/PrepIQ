import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

print("=== Available Routes ===")
for route in app.routes:
    if hasattr(route, 'methods'):
        for method in route.methods:
            print(f"{method} {route.path}")
    else:
        print(f"GET {route.path}")

print("\n=== Looking for auth routes ===")
auth_routes = [route for route in app.routes if hasattr(route, 'path') and '/auth' in route.path]
for route in auth_routes:
    if hasattr(route, 'methods'):
        for method in route.methods:
            print(f"FOUND: {method} {route.path}")
    else:
        print(f"FOUND: GET {route.path}")