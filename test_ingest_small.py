#!/usr/bin/env python3
"""
Test ingestion with just 2-3 PDF files to verify the pipeline works
"""
import aiohttp
import asyncio
import os
import json

IPADDRESS = "0.0.0.0"
INGESTOR_SERVER_PORT = "8082"
BASE_URL = f"http://{IPADDRESS}:{INGESTOR_SERVER_PORT}"
NGC_API_KEY = "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"

os.environ["NVIDIA_API_KEY"] = NGC_API_KEY
os.environ["NGC_CLI_API_KEY"] = NGC_API_KEY
os.environ["NGC_API_KEY"] = NGC_API_KEY

DATA_DIR = "/home/milos/eragbpv2/rag/data/SPH"

async def print_response(response):
    try:
        response_json = await response.json()
        print(json.dumps(response_json, indent=2))
        return response_json
    except:
        text = await response.text()
        print(text)
        return text

async def upload_test_documents(collection_name: str = "SPH"):
    """Upload just 3 test documents."""
    print(f"=== Testing Upload to '{collection_name}' Collection ===")
    
    # Get just first 3 PDF files
    all_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) 
                 if os.path.isfile(os.path.join(DATA_DIR, f)) and f.endswith('.pdf')]
    files = all_files[:3]  # Just first 3
    
    print(f"Testing with {len(files)} PDF files:")
    for f in files:
        print(f"  - {os.path.basename(f)}")
    print()

    data = {
        "collection_name": collection_name,
        "extraction_options": {
            "extract_text": True,
            "extract_tables": True,
            "extract_charts": True,
            "extract_images": False,
            "extract_method": "pdfium",
            "text_depth": "page",
        },
        "split_options": {
            "chunk_size": 1024,
            "chunk_overlap": 150
        }
    }

    form_data = aiohttp.FormData()
    for file_path in files:
        form_data.add_field("documents", open(file_path, "rb"), 
                          filename=os.path.basename(file_path), 
                          content_type="application/pdf")

    form_data.add_field("data", json.dumps(data), content_type="application/json")

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
        try:
            print("Uploading test batch... (may take a few minutes)")
            async with session.post(f"{BASE_URL}/v1/documents", data=form_data) as response:
                result = await print_response(response)
                return result
        except Exception as e:
            print(f"Error: {e}")
            return None

async def list_documents(collection_name: str = "SPH"):
    """List documents in collection."""
    print(f"\n=== Documents in '{collection_name}' ===")
    url = f"{BASE_URL}/v1/documents"
    params = {"collection_name": collection_name}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                return await print_response(response)
        except Exception as e:
            print(f"Error: {e}")
            return None

async def main():
    print("=" * 70)
    print("Testing SPH Document Ingestion (3 files)")
    print("=" * 70)
    print()
    
    # Upload test batch
    await upload_test_documents(collection_name="SPH")
    
    # List to verify
    await list_documents(collection_name="SPH")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())

