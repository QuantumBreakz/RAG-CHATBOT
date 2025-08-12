#!/usr/bin/env python3
"""
Script to fix the filtering threshold in backend/api.py
"""

def fix_filtering():
    """Fix the confidence threshold in the filtering logic"""
    
    file_path = "backend/api.py"
    
    try:
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace the confidence threshold from 0.5 to 0.85 (85%)
        old_threshold = "if confidence > 0.5:  # Only include high-confidence sources"
        new_threshold = "if confidence > 0.85:  # Only include high-confidence sources"
        
        if old_threshold in content:
            content = content.replace(old_threshold, new_threshold)
            
            # Write back to file
            with open(file_path, 'w') as f:
                f.write(content)
            
            print("✅ Successfully updated confidence threshold from 0.5 to 0.85 (85%)")
            print("   This should significantly improve filtering and reduce irrelevant chunks")
        else:
            print("❌ Could not find the threshold to replace")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    fix_filtering()
