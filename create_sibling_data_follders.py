import os

# Get directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Go one level up (parent directory, expected to be the parent for pipeline as a whole)
parent_dir = os.path.dirname(script_dir)

# Main directory to create
base_data_dir = os.path.join(parent_dir, "kosloff-abdulghani-cavity-pipeline-data")

# Create main directory
os.makedirs(base_data_dir, exist_ok=True)

# Subdirectories to create
subdirs = ["input", "output", "PM_INPUT", "PM_OUTPUT"]

# Create subdirectories
for subdir in subdirs:
    os.makedirs(os.path.join(base_data_dir, subdir), exist_ok=True)

print(f"Data directory structure created under: {base_data_dir}")