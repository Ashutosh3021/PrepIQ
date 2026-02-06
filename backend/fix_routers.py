import os
import fileinput

# List of routers that need to be fixed
routers_to_fix = [
    'analysis.py',
    'chat.py', 
    'papers.py',
    'plans.py',
    'predictions.py',
    'questions.py',
    'tests.py',
    'wizard.py'
]

# The import replacement
old_import = "from ..routers.auth import get_current_user"
new_import = """import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import from the new Supabase-first auth service
from services.supabase_first_auth import get_current_user_from_token

# Dependency for protected routes
async def get_current_user(authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)"""

router_dir = 'app/routers'

for router_file in routers_to_fix:
    file_path = os.path.join(router_dir, router_file)
    if os.path.exists(file_path):
        print(f"Fixing {router_file}...")
        
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace the import
        if old_import in content:
            # Find the position of the old import
            lines = content.split('\n')
            new_lines = []
            import_replaced = False
            
            for line in lines:
                if old_import in line and not import_replaced:
                    # Replace the import line with new imports and function
                    new_lines.extend(new_import.split('\n'))
                    import_replaced = True
                else:
                    new_lines.append(line)
            
            # Write the updated content
            with open(file_path, 'w') as f:
                f.write('\n'.join(new_lines))
            
            print(f"  ✓ Fixed {router_file}")
        else:
            print(f"  - No changes needed for {router_file}")
    else:
        print(f"  ✗ File {router_file} not found")

print("\nAll routers have been updated!")