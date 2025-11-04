# Configuration Gaps Analysis
## Hybrid RAG vs Official NVIDIA RAG Blueprint

Reference: [https://github.com/stanicm/rag/tree/main](https://github.com/stanicm/rag/tree/main)

---

## 🚨 CRITICAL MISSING CONFIGURATIONS

### INGESTOR-SERVER

#### 1. **Shared Memory (CRITICAL)**
```yaml
shm_size: 5gb  # Required for large document processing
```

#### 2. **NV-Ingest Extraction Settings**
```yaml
APP_NVINGEST_EXTRACTTEXT: True
APP_NVINGEST_EXTRACTTABLES: True
APP_NVINGEST_EXTRACTCHARTS: True
APP_NVINGEST_EXTRACTINFOGRAPHICS: False
APP_NVINGEST_EXTRACTIMAGES: False
APP_NVINGEST_EXTRACTPAGEASIMAGE: False
APP_NVINGEST_TEXTDEPTH: page  # "page" or "document"
APP_NVINGEST_PDFEXTRACTMETHOD: None  # pdfium, nemoretriever_parse, or None
```

#### 3. **NV-Ingest Chunking/Splitting**
```yaml
APP_NVINGEST_CHUNKSIZE: 512
APP_NVINGEST_CHUNKOVERLAP: 150
APP_NVINGEST_ENABLEPDFSPLITTER: True
```

#### 4. **Batch Processing**
```yaml
NV_INGEST_FILES_PER_BATCH: 16
NV_INGEST_CONCURRENT_BATCHES: 4
```

#### 5. **MinIO & Storage**
```yaml
ENABLE_MINIO_BULK_UPLOAD: True
NVINGEST_MINIO_BUCKET: nv-ingest
TEMP_DIR: /tmp-data
INGESTOR_SERVER_DATA_DIR: /data/
```

#### 6. **Redis Configuration**
```yaml
REDIS_DB: 0
```

#### 7. **Vector Store GPU Acceleration**
```yaml
APP_VECTORSTORE_SEARCHTYPE: dense  # or "hybrid"
APP_VECTORSTORE_ENABLEGPUINDEX: True
APP_VECTORSTORE_ENABLEGPUSEARCH: True
```

#### 8. **Logging & Optional Features**
```yaml
LOGLEVEL: INFO
ENABLE_CITATIONS: True
```

---

### NV-INGEST-MS-RUNTIME

#### 1. **Redis Task Queue** (CRITICAL)
```yaml
REDIS_MORPHEUS_TASK_QUEUE: morpheus_task_queue
MINIO_BUCKET: nv-ingest
```

#### 2. **Inference Protocol Settings**
Currently using HTTP endpoints, but official uses **GRPC** for better performance:
```yaml
# Page Elements
YOLOX_GRPC_ENDPOINT: page-elements:8001
YOLOX_HTTP_ENDPOINT: http://page-elements:8000/v1/infer
YOLOX_INFER_PROTOCOL: grpc  # We're using http

# Graphic Elements  
YOLOX_GRAPHIC_ELEMENTS_GRPC_ENDPOINT: graphic-elements:8001
YOLOX_GRAPHIC_ELEMENTS_HTTP_ENDPOINT: http://graphic-elements:8000/v1/infer
YOLOX_GRAPHIC_ELEMENTS_INFER_PROTOCOL: grpc  # We're using http

# Table Structure
YOLOX_TABLE_STRUCTURE_GRPC_ENDPOINT: table-structure:8001
YOLOX_TABLE_STRUCTURE_HTTP_ENDPOINT: http://table-structure:8000/v1/infer
YOLOX_TABLE_STRUCTURE_INFER_PROTOCOL: grpc  # We're using http

# OCR
OCR_GRPC_ENDPOINT: (for local) or use NVIDIA API
OCR_HTTP_ENDPOINT: https://ai.api.nvidia.com/v1/cv/baidu/paddleocr
OCR_INFER_PROTOCOL: http  # When using NVIDIA API
OCR_MODEL_NAME: paddle
```

#### 3. **Performance & Scaling**
```yaml
MAX_INGEST_PROCESS_WORKERS: 16
INGEST_LOG_LEVEL: WARNING
INGEST_RAY_LOG_LEVEL: PRODUCTION
INGEST_EDGE_BUFFER_SIZE: 64
INGEST_DYNAMIC_MEMORY_THRESHOLD: 0.8
INGEST_DISABLE_DYNAMIC_SCALING: True
NV_INGEST_MAX_UTIL: 48
```

#### 4. **CUDA & System**
```yaml
CUDA_VISIBLE_DEVICES: 0
MRC_IGNORE_NUMA_CHECK: 1
READY_CHECK_ALL_COMPONENTS: False
```

#### 5. **Healthcheck** (MISSING)
```yaml
healthcheck:
  test: curl --fail http://nv-ingest-ms-runtime:7670/v1/health/ready || exit 1
  interval: 10s
  timeout: 5s
  retries: 20
```

---

## 📋 RECOMMENDED FIXES

### Priority 1 (Apply Immediately)
1. Add `shm_size: 5gb` to ingestor-server
2. Add `REDIS_MORPHEUS_TASK_QUEUE: morpheus_task_queue` to nv-ingest-ms-runtime
3. Add NV-Ingest extraction settings to ingestor-server
4. Add chunking/splitting settings to ingestor-server
5. Add batch processing settings to ingestor-server

### Priority 2 (Performance)
1. Switch from HTTP to GRPC for local NIMs
2. Add performance tuning parameters to nv-ingest-ms-runtime
3. Add healthcheck to nv-ingest-ms-runtime

### Priority 3 (Optional)
1. Add GPU acceleration flags for vector store
2. Add logging configuration
3. Add citation support

---

## 🔧 IMPLEMENTATION PLAN

**Step 1**: Update ingestor-server with critical missing env vars
**Step 2**: Update nv-ingest-ms-runtime with Redis task queue
**Step 3**: Restart both services
**Step 4**: Re-test document ingestion
**Step 5**: (Optional) Switch to GRPC for local NIMs if needed

---

## ⚠️ NOTES

- **GRPC vs HTTP**: Official uses GRPC (port 8001) for local NIMs, we're using HTTP (port 8000)
  - GRPC is faster but more complex
  - HTTP is simpler and should work fine
  - Can switch later if performance is an issue

- **Embedding dimensions**: 
  - Official uses 2048 for local embedding models
  - We're using 1024 for NVIDIA API (nv-embedqa-e5-v5)
  - This is correct for our hybrid setup

- **MinIO endpoints**:
  - Official: `minio:9010` 
  - Ours: `milvus-minio:9000`
  - Both should work if consistent

