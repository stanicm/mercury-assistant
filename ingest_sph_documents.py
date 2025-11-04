#!/usr/bin/env python3
"""
SPH Document Ingestion Script
Ingests PDF documents from the SPH folder into the RAG system
"""

import requests
import json
import os
from pathlib import Path

# Configuration
INGESTOR_URL = "http://localhost:8082/documents"
COLLECTION_NAME = "SPH"
SPH_DATA_DIR = "/home/milos/eragbpv2/rag/data/SPH"

# Select first 3 PDF files
pdf_files = sorted(Path(SPH_DATA_DIR).glob("*.pdf"))[:3]

print("=" * 80)
print("SPH Document Ingestion")
print("=" * 80)
print(f"\nCollection: {COLLECTION_NAME}")
print(f"Ingestor URL: {INGESTOR_URL}")
print(f"\nDocuments to ingest ({len(pdf_files)}):")
for i, pdf in enumerate(pdf_files, 1):
    print(f"  {i}. {pdf.name} ({pdf.stat().st_size / 1024 / 1024:.2f} MB)")

print("\n" + "-" * 80)

# Ingest each document
for i, pdf_file in enumerate(pdf_files, 1):
    print(f"\n[{i}/{len(pdf_files)}] Ingesting: {pdf_file.name}")
    print("-" * 80)
    
    try:
        # Prepare the request
        files = {
            'documents': (pdf_file.name, open(pdf_file, 'rb'), 'application/pdf')
        }
        
        data = json.dumps({
            "collection_name": COLLECTION_NAME,
            "metadata": {
                "filename": pdf_file.name,
                "category": "SPH_Research"
            }
        })
        
        form_data = {
            'data': (None, data, 'application/json')
        }
        
        # Send the request
        print(f"  → Uploading to {INGESTOR_URL}...")
        response = requests.post(
            INGESTOR_URL,
            files={**files, **form_data},
            timeout=300  # 5 minutes timeout for large documents
        )
        
        print(f"  → Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Success!")
            if 'message' in result:
                print(f"     Message: {result['message']}")
            if 'num_entities' in result:
                print(f"     Entities: {result['num_entities']}")
        else:
            print(f"  ❌ Failed!")
            print(f"     Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    finally:
        # Close file if it was opened
        try:
            files['documents'][1].close()
        except:
            pass

print("\n" + "=" * 80)
print("Ingestion Complete!")
print("=" * 80)

# Check final collection status
print("\nChecking collection status...")
try:
    response = requests.get("http://localhost:8082/v1/collections")
    if response.status_code == 200:
        collections = response.json().get('collections', [])
        sph_collection = next((c for c in collections if c['collection_name'] == 'SPH'), None)
        if sph_collection:
            print(f"✅ SPH Collection: {sph_collection['num_entities']} entities")
    else:
        print(f"⚠️  Could not retrieve collection status")
except Exception as e:
    print(f"⚠️  Error checking status: {e}")

print("")
