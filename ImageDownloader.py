import os
import zipfile
import gdown
from pathlib import Path

def download_and_extract_zips(folder_url, output_dir="downloads"):
    """
    Downloads all zip files from a Google Drive folder and extracts them.
    Uses the parent folder name (not zip file name) for extraction.
    
    Args:
        folder_url: Google Drive folder URL
        output_dir: Base directory to save and extract files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract folder ID from URL
    if "folders/" in folder_url:
        folder_id = folder_url.split("folders/")[1].split("?")[0]
    else:
        folder_id = folder_url
    
    print(f"Downloading files from folder: {folder_id}")
    
    # Download all files from the folder
    gdown.download_folder(
        id=folder_id,
        output=output_dir,
        quiet=False,
        use_cookies=False
    )
    
    print("\n" + "="*50)
    print("Extracting zip files...")
    print("="*50 + "\n")
    
    # Find all zip files in the output directory
    zip_files = list(Path(output_dir).rglob("*.zip"))
    
    if not zip_files:
        print("No zip files found in the downloaded folder.")
        return
    
    # Process each zip file
    for zip_path in zip_files:
        # Get the parent folder name (e.g., "bob" from "bob/bob1111.zip")
        parent_folder_name = zip_path.parent.name
        
        # If the zip is directly in output_dir, use zip name instead
        if zip_path.parent == Path(output_dir):
            parent_folder_name = zip_path.stem
        
        # Create extraction folder path in the output directory
        extract_path = Path(output_dir) / parent_folder_name
        
        print(f"Extracting: {zip_path.name}")
        print(f"   From folder: {zip_path.parent.name}")
        print(f"   -> To: {extract_path}")
        
        try:
            # Create the folder if it doesn't exist
            extract_path.mkdir(parents=True, exist_ok=True)
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            print(f"   ✓ Successfully extracted {len(zip_ref.namelist())} files")
            
            # Remove the zip file after extraction
            zip_path.unlink()
            print(f"   ✓ Deleted zip file")
            
            # Remove the now-empty parent folder if it's not the output directory
            if zip_path.parent != Path(output_dir) and not any(zip_path.parent.iterdir()):
                zip_path.parent.rmdir()
                print(f"   ✓ Removed empty folder: {zip_path.parent.name}")
            
        except zipfile.BadZipFile:
            print(f"   ✗ Error: {zip_path.name} is not a valid zip file")
        except Exception as e:
            print(f"   ✗ Error extracting {zip_path.name}: {str(e)}")
        
        print()
    
    print("="*50)
    print("Extraction complete!")
    print("="*50)

if __name__ == "__main__":
    # Your Google Drive folder URL
    url = "https://drive.google.com/drive/folders/1pZBcKW5CpQORjYXAnPZrHHeV0MtWNTHx"
    
    # Download and extract all zip files
    download_and_extract_zips(url, output_dir="Faces")
    
    print("\nAll files have been downloaded and extracted!")
    print("Check the 'Students' folder for the extracted contents.")