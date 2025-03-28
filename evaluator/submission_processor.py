import os
import zipfile
import shutil

class SubmissionProcessor:
    def extract_submission(self, zip_file_path: str, extraction_dir: str):
        """
        Safely extract submission zip maintaining directory structure
        
        :param zip_file_path: Path to zip file
        :param extraction_dir: Directory to extract files
        """
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Prevent zip bomb and path traversal
            for file in zip_ref.namelist():
                if file.startswith('__MACOSX/') or file.endswith('/') or '..' in file:
                    continue

                # Ensure the extracted path is within the intended directory
                target_path = os.path.join(extraction_dir, file)
                abs_target_path = os.path.abspath(target_path)
                if not abs_target_path.startswith(os.path.abspath(extraction_dir)):
                    raise ValueError("Attempted Path Traversal Detected")
                    
                # Create directories if needed
                target_path = os.path.join(extraction_dir, file)
                target_dir = os.path.dirname(target_path)
                
                # Create directory structure if it doesn't exist
                os.makedirs(target_dir, exist_ok=True)
                
                # Skip if it's a directory (already handled)
                if os.path.basename(file) == '':
                    continue
                    
                # Extract files safely
                source = zip_ref.open(file)
                with open(target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
                source.close()