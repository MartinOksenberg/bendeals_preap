import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import tempfile

# Import the core processing logic from main.py
from main import process_credit_report

app = FastAPI(
    title="Credit Report Processing Service",
    description="An API that receives a URL to a PDF credit report, processes it, and returns a JSON analysis.",
    version="1.1.0"
)

class ReportRequest(BaseModel):
    file_url: HttpUrl

def download_file(url: str, prefix: str = 'downloaded-', suffix: str = '.pdf') -> str:
    """
    Downloads a file from a URL to a temporary local path.
    Returns the path to the downloaded file.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        with tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix) as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            return tmp_file.name
            
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to download or access the file from the provided URL: {e}")

@app.post("/process-report/", tags=["Credit Report Processing"])
async def process_report_from_url(request: ReportRequest):
    """
    Receives a URL to a PDF file, downloads it, processes it through the pipeline,
    and returns the final JSON analysis.
    """
    tmp_path = None
    try:
        # 1. Download the file from the Supabase Storage URL
        print(f"Downloading file from URL: {request.file_url}")
        tmp_path = download_file(str(request.file_url))
        
        # 2. Run the main processing logic on the downloaded file
        print(f"Processing temporary file: {tmp_path}")
        analysis_json = process_credit_report(tmp_path)
        
        if not analysis_json:
            raise HTTPException(status_code=500, detail="The analysis process returned no data.")

        # 3. Return the final JSON analysis
        return analysis_json

    except Exception as e:
        # Re-raise HTTPExceptions to let FastAPI handle them
        if isinstance(e, HTTPException):
            raise
        # Wrap other exceptions in a standard 500 error
        print(f"An unexpected error occurred during processing: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
    finally:
        # 4. Clean up the temporary downloaded file
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path) 