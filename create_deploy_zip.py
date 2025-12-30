import zipfile
import os

files_to_zip = [
    "app.py",
    "search_maamar_with_openai.py",
    "requirements.txt",
    "Dockerfile",
    "2_maamarim_unified.pkl.gz",
    "deploy.sh",
    ".dockerignore",
    "DEPLOYMENT_GUIDE.md",
    "QUERY_GUIDE.md",
    "env"
]

output_zip = "maamar-search-deploy.zip"

print(f"Creating {output_zip}...")

with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in files_to_zip:
        if os.path.exists(file):
            print(f"Adding {file}...")
            # If it's the 2_maamarim file, we can optionally rename it inside the zip 
            # or keep it as is. Dockerfile expects 2_maamarim_unified.pkl.gz, so we keep it.
            zipf.write(file)
        else:
            print(f"⚠️ Warning: {file} not found!")

print("✅ Done! Zip file created successfully.")

