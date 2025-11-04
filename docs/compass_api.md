# API Documentation

## Overview

The 追憶のコンパス API is built with FastAPI and provides endpoints for managing and searching memory records stored in LanceDB.

**Base URL:** `http://localhost:8000`

**API Version:** 2.7.2

**Chat API Version:** 1.3.0 (Multimodal support added)

**Architecture:** Fully refactored with modular routers, service layer, dependency injection, comprehensive error handling, and DRY principles (Phases 1-6 complete)

## Authentication

**As of version 2.2.1**, all API endpoints require Bearer token authentication.

**Authentication Header:**
```
Authorization: Bearer <COMPASS_API_KEY>
```

**Setup:**
1. Set `COMPASS_API_KEY` in your `.env` file
2. Include the `Authorization` header in all API requests
3. If `COMPASS_API_KEY` is not set, authentication is skipped (development mode only)

**Authentication Error Response:**
```json
{
  "detail": "Authorization header is missing or invalid."
}
```

**Status Code:** `401 Unauthorized`

## Interactive Documentation

FastAPI provides auto-generated interactive documentation:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Code Architecture (v2.7.0)

The API has undergone comprehensive refactoring (Phases 1-6) resulting in a clean, maintainable architecture:

### Directory Structure

```
api/
├── main.py                 # Application entry point (97 lines)
├── config.py              # Centralized configuration (Phase 1)
├── dependencies.py        # Dependency injection functions (Phase 2)
├── exceptions.py          # Custom exception classes (Phase 5)
├── models.py              # Common data models (Phase 6)
├── services/              # Business logic layer (Phase 3)
│   ├── __init__.py
│   ├── embedding_service.py
│   ├── search_service.py
│   ├── memory_service.py
│   ├── gemini_service.py
│   └── ollama_service.py
├── routers/               # API endpoints by domain (Phase 4)
│   ├── __init__.py
│   ├── search.py          # Search endpoints
│   ├── memory.py          # CRUD endpoints
│   └── chat.py            # Chat endpoints
└── utils/                 # Shared utilities (Phase 6)
    ├── __init__.py
    └── data_transform.py  # Data transformation functions
```

### Architectural Layers

```
┌─────────────────────────────────────────────┐
│         FastAPI Application (main.py)        │
│  - Global exception handlers                │
│  - CORS middleware                          │
│  - Router registration                      │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│            Routers (routers/)               │
│  - Endpoint definitions by domain           │
│  - Request/response validation              │
│  - Uses dependency injection                │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│          Service Layer (services/)          │
│  - Business logic implementation            │
│  - Domain-specific operations               │
│  - Raises custom exceptions                 │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│    Infrastructure (dependencies.py)         │
│  - Database connections                     │
│  - Model initialization                     │
│  - External API clients                     │
└─────────────────────────────────────────────┘
```

### Key Design Principles

1. **Configuration Management (Phase 1)**
   - All configuration centralized in `config.py`
   - Environment variable support via Pydantic Settings
   - Type-safe configuration

2. **Dependency Injection (Phase 2)**
   - No global variables
   - Testable components
   - FastAPI's `Depends()` pattern throughout

3. **Service Layer (Phase 3)**
   - Business logic separated from endpoints
   - Reusable services
   - Clear responsibilities

4. **Modular Routers (Phase 4)**
   - Endpoints organized by domain
   - 92% reduction in main.py (625 → 49 lines)
   - Domain-specific tags for documentation

5. **Error Handling (Phase 5)**
   - 18 custom exception classes
   - Global exception handlers
   - Consistent error responses

6. **DRY Principles (Phase 6)**
   - Common models in `models.py`
   - Shared utilities in `utils/`
   - Eliminated 128 lines of duplicate code

### Refactoring Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| main.py size | 625 lines | 97 lines | -84% |
| Code duplication | High | Minimal | -128 lines |
| Total codebase | +376 lines reduction | N/A | Better organization |
| Maintainability | Low | High | Dramatic |
| Testability | Difficult | Easy | Much improved |
| Error handling | Inconsistent | Unified | Production-ready |

## Data Models

### MemoryRecord

Represents a single memory entry in the database.

```typescript
{
  id: string;
  summary: string;
  content: string;
  timestamp: string | null;
  speaker: string[] | null;
  source_file: string;
  relationships: {
    target_id: string;
    type: string;
    weight: number;
  }[];
  entities: {
    name: string;
    type: string;
  }[];
}
```

### SearchRequest

```typescript
{
  text: string;            // Search query
  config: {
    target: "summary" | "content";  // Which field to search
    limit: number;         // Max results (default: 3)
    compress: boolean;     // Enable AI summarization (default: false)
  }
}
```

### GraphSearchRequest

```typescript
{
  text: string;            // Search query
  config: {
    target: "summary" | "content";
    limit: number;         // Number of initial results (X)
    compress: boolean;
    related_limit: number; // Number of related items to fetch per result (Y)
  }
}
```

### ListRequest

```typescript
{
  limit: number            // Max records (1-1000, default: 100)
  offset: number           // Skip N records (default: 0)
  start_date?: string      // Optional start date filter (YYYY-MM-DD)
  end_date?: string        // Optional end date filter (YYYY-MM-DD)
}
```

### UpdateRequest

```typescript
{
  summary: string
  content: string
  timestamp: string
  speakers: string[]
}
```

### ChatImagePart (v1.3.0)

```typescript
{
  mime_type: string;  // Image MIME type (e.g., "image/jpeg", "image/png")
  data: string;       // Base64-encoded image data
}
```

### ChatMessage (v1.3.0: Image Support Added)

```typescript
{
  role: "user" | "model";
  content: string;                          // Text content (default: "")
  images?: ChatImagePart[];                 // Optional images (v1.3.0)
}
```

### MemorySearchConfig

```typescript
{
  enabled: boolean;           // Enable memory search (default: true)
  target: "summary" | "content";  // Search target (default: "content")
  limit: number;              // Max memories to retrieve (default: 3)
  search_type: "normal" | "graph";  // Search type (default: "normal")
}
```

### GeminiParams

```typescript
{
  temperature?: number;        // 0.0-2.0 (optional)
  max_output_tokens?: number;  // Max output tokens (optional)
  top_p?: number;              // 0.0-1.0 (optional)
  top_k?: number;              // Top-k sampling (optional)
}
```

### ChatGeminiConfig

```typescript
{
  model: string;                         // Gemini model name (default: "gemini-2.0-flash-exp")
  memory_search_config: MemorySearchConfig;
  gemini_params: GeminiParams;
}
```

### ChatGeminiRequest

```typescript
{
  messages: ChatMessage[];     // Conversation history
  config: ChatGeminiConfig;    // Configuration
}
```

### ChatGeminiResponse

```typescript
{
  status: "success";
  response: {
    role: "model";
    content: string;           // AI-generated response
  };
  debug_info: {
    search_query?: string;
    retrieved_memory_ids: string[];
    context_structure: Array<{
      type: string;
      truncated: boolean;
      count?: number;
    }>;
    final_prompt_preview?: string;
    gemini_request_token_count?: number;
    gemini_response_token_count?: number;
  };
}
```

## Endpoints

### GET /

**Description:** Root endpoint with welcome message

**Response:**
```json
{
  "message": "追憶のコンパス - 検索APIへようこそ！ /docs にアクセスしてAPIドキュメントを確認してください。"
}
```

---

### POST /search

**Description:** Search memories using vector similarity search

**Authentication:** Required (`Authorization: Bearer <COMPASS_API_KEY>`)

**Request Headers:**
```
Authorization: Bearer your-compass-api-key-here
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "検索したいキーワード",
  "config": {
    "target": "summary",
    "limit": 10,
    "compress": false
  }
}
```

**Parameters:**
- `text` (required): Search query string
- `config.target` (optional): Search on "summary" or "content" vectors (default: "summary")
- `config.limit` (optional): Number of results to return (default: 3)
- `config.compress` (optional): Use Ollama to compress all results into one summary (default: false)

**Response:**
```json
{
  "results": [
    {
      "id": "uuid-here",
      "summary": "記憶の要約",
      "content": "記憶の内容",
      "timestamp": "2025-10-08T12:00:00",
      "speaker": ["ありす", "ご主人様"],
      "source_file": "2025-10-08.md",
      "relationships": [
        {
          "target_id": "related-uuid-1",
          "type": "similar_to",
          "weight": 0.85
        }
      ],
      "entities": []
    }
  ],
  "compressed": false,
  "compressed_text": null
}
```

**Response (with compression):**
```json
{
  "results": [...],
  "compressed": true,
  "compressed_text": "全検索結果の要約がここに..."
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication
- `503 Service Unavailable`: Database not available
- `500 Internal Server Error`: Search processing error

**Example Usage:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-compass-api-key-here" \
  -d '{
    "text": "ありすとの会話",
    "config": {
      "target": "content",
      "limit": 5,
      "compress": true
    }
  }'
```

--- 

### POST /graph_search

**Description:** Performs a graph search, retrieving memories similar to the query and also memories related to those results.

**Authentication:** Required (`Authorization: Bearer <COMPASS_API_KEY>`)

**Request Headers:**
```
Authorization: Bearer your-compass-api-key-here
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "検索したいキーワード",
  "config": {
    "target": "summary",
    "limit": 5,
    "compress": false,
    "related_limit": 3
  }
}
```

**Parameters:**
- All parameters from `/search`.
- `config.related_limit` (optional): Number of related memories to retrieve for each initial result (default: 3).

**Response:**
- The response format is identical to `/search`, containing a list of `MemoryRecord` objects.

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication
- `503 Service Unavailable`: Database not available
- `500 Internal Server Error`: Search processing error

**Example Usage:**
```bash
curl -X POST http://localhost:8000/graph_search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-compass-api-key-here" \
  -d '{
    "text": "ありすとの会話",
    "config": {
      "target": "content",
      "limit": 5,
      "related_limit": 2
    }
  }'
```

---

### POST /list

**Description:** Retrieve a paginated list of all memory records

**Authentication:** Required (`Authorization: Bearer <COMPASS_API_KEY>`)

**Request Headers:**
```
Authorization: Bearer your-compass-api-key-here
Content-Type: application/json
```

**Request Body:**
```json
{
  "limit": 100,
  "offset": 0,
  "start_date": "2025-10-01",
  "end_date": "2025-10-31"
}
```

**Parameters:**
- `limit` (optional): Max records to return (1-1000, default: 100)
- `offset` (optional): Number of records to skip (default: 0)
- `start_date` (optional): Filter by start date in YYYY-MM-DD format (inclusive)
- `end_date` (optional): Filter by end date in YYYY-MM-DD format (inclusive)

**Response:**
```json
{
  "records": [
    {
      "id": "uuid-here",
      "summary": "記憶の要約",
      "content": "記憶の内容",
      "timestamp": "2025-10-08T12:00:00",
      "speaker": ["ありす"],
      "source_file": "2025-10-08.md",
      "relationships": [],
      "entities": []
    }
  ],
  "total": 1500,
  "offset": 0,
  "limit": 100
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication
- `400 Bad Request`: Invalid date format
- `503 Service Unavailable`: Database not available
- `500 Internal Server Error`: List processing error

**Example Usage:**
```bash
curl -X POST http://localhost:8000/list \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-compass-api-key-here" \
  -d '{
    "limit": 20,
    "offset": 0,
    "start_date": "2025-10-01",
    "end_date": "2025-10-31"
  }'
```

---

### PUT /update/{record_id}

**Description:** Update an existing memory record

**Authentication:** Required (`Authorization: Bearer <COMPASS_API_KEY>`)

**Request Headers:**
```
Authorization: Bearer your-compass-api-key-here
Content-Type: application/json
```

**Path Parameters:**
- `record_id` (required): ID of the record to update

**Request Body:**
```json
{
  "summary": "新しい要約",
  "content": "新しい内容",
  "timestamp": "2025-10-08T12:00:00",
  "speakers": ["ありす", "ご主人様"]
}
```

**Response:**
```json
{
  "message": "ID 'uuid-here' のレコードが正常に更新されました。"
}
```

**Behavior:**
- If `summary` or `content` is changed, the corresponding vector embeddings are automatically regenerated
- The original record is deleted and a new one is added with the same ID
- Metadata is updated with new speakers list

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Record with given ID not found
- `503 Service Unavailable`: Database not available
- `500 Internal Server Error`: Update processing error

**Example Usage:**
```bash
curl -X PUT http://localhost:8000/update/abc-123 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-compass-api-key-here" \
  -d '{
    "summary": "Updated summary",
    "content": "Updated content",
    "timestamp": "2025-10-08T15:30:00",
    "speakers": ["ありす"]
  }'
```

---

### DELETE /delete/{record_id}

**Description:** Delete a memory record

**Authentication:** Required (`Authorization: Bearer <COMPASS_API_KEY>`)

**Request Headers:**
```
Authorization: Bearer your-compass-api-key-here
```

**Path Parameters:**
- `record_id` (required): ID of the record to delete

**Response:**
- Status: `204 No Content` (on success)

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication
- `503 Service Unavailable`: Database not available
- `500 Internal Server Error`: Deletion error

**Example Usage:**
```bash
curl -X DELETE http://localhost:8000/delete/abc-123 \
  -H "Authorization: Bearer your-compass-api-key-here"
```

---

### POST /chat/gemini

**Description:** Chat with Gemini API integrated with memory context retrieval. Searches for relevant memories and provides context-aware responses. **v1.3.0: Now supports multimodal input (images)!**

**Authentication:** Required (`Authorization: Bearer <COMPASS_API_KEY>`)

**Note:** Uses the same unified authentication system as all other endpoints (v2.2.1+)

**v1.3.0 Features:**
- 📷 **Multimodal Support**: Send images along with text messages
- 🔄 **Automatic Image Resizing**: Server-side optimization to reduce API costs
- 🎯 **Image Token Calculation**: Accurate token counting for images (768px tile-based)

**Request Headers:**
```
Authorization: Bearer your-compass-api-key-here
Content-Type: application/json
```

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "こんにちは、ありす。"
    },
    {
      "role": "model",
      "content": "こんにちは、ご主人様！"
    },
    {
      "role": "user",
      "content": "今日の調子はどう?"
    }
  ],
  "config": {
    "model": "gemini-2.0-flash-exp",
    "memory_search_config": {
      "enabled": true,
      "target": "content",
      "limit": 3,
      "search_type": "normal"
    },
    "gemini_params": {
      "temperature": 0.7,
      "max_output_tokens": 1024
    }
  }
}
```

**Request Body with Image (v1.3.0):**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "この画像には何が描かれていますか？",
      "images": [
        {
          "mime_type": "image/jpeg",
          "data": "/9j/4AAQSkZJRgABAQEA..."
        }
      ]
    }
  ],
  "config": {
    "model": "gemini-2.5-flash"
  }
}
```

**Minimal Request Body (all config fields are optional):**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "こんにちは、ありす。"
    }
  ]
}
```

**Parameters:**
- `messages` (required): Array of conversation messages with role (user/model), content, and optional images (v1.3.0)
- `config` (optional): Configuration object with defaults for all fields
- `config.model` (optional): Gemini model to use (default: "gemini-2.0-flash-exp")
- `config.memory_search_config` (optional): Memory search configuration (default: enabled with content search)
  - `enabled` (optional): Enable memory search (default: true)
  - `target` (optional): Search on "summary" or "content" (default: "content")
  - `limit` (optional): Max memories to retrieve (default: 3)
  - `search_type` (optional): "normal" or "graph" search (default: "normal")
- `config.gemini_params` (optional): Gemini API parameters (all fields optional)
  - `temperature` (optional): Gemini temperature parameter (0.0-2.0)
  - `max_output_tokens` (optional): Max output tokens
  - `top_p` (optional): Top-p sampling (0.0-1.0)
  - `top_k` (optional): Top-k sampling

**Response (Success):**
```json
{
  "status": "success",
  "response": {
    "role": "model",
    "content": "はい、ご主人様！今日も元気に動作していますよ。"
  },
  "debug_info": {
    "search_query": "今日の調子はどう?",
    "retrieved_memory_ids": ["uuid-abc-123", "uuid-def-456"],
    "context_structure": [
      {
        "type": "long_term_memory",
        "truncated": false
      },
      {
        "type": "retrieved_memories",
        "count": 2,
        "truncated": false
      },
      {
        "type": "session_history",
        "count": 3,
        "truncated": false
      }
    ],
    "final_prompt_preview": "=== 長期記憶 ===\nあなたは「ありす」という名前のAIアシスタントです...",
    "gemini_request_token_count": 250,
    "gemini_response_token_count": 45
  }
}
```

**Response (Error):**
```json
{
  "status": "error",
  "error": {
    "code": "authentication_failed",
    "message": "Invalid API key."
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication (standard HTTPException response)
- `gemini_auth_error`: Gemini API client not initialized (check GOOGLE_API_KEY)
- `config_error`: Failed to load system prompt or configuration
- `gemini_api_error`: Error calling Gemini API

**Note:** As of v2.2.1, authentication errors return a standard 401 HTTPException instead of a custom error response.

**Features:**
- **Memory Search Integration:** Automatically searches for relevant memories based on the last user message
- **Context Management:** Loads system prompt and long-term memory from files
- **Token Management:** Automatically trims context if token limit is exceeded
- **Conversation Logging:** Saves conversation to `data/dialog/api-YYYY-MM-DD.md`
- **Debug Information:** Returns detailed debug info including token counts and retrieved memory IDs

**Environment Configuration:**
Create a `.env` file in the project root with:
```env
GOOGLE_API_KEY=your-google-api-key-here
COMPASS_API_KEY=your-compass-api-key-here
SYSTEM_PROMPT_PATH=data/prompts/system_prompt.txt
LONG_TERM_MEMORY_PATH=data/prompts/long_term_memory.txt
```

**Example Usage:**
```bash
curl -X POST http://localhost:8000/chat/gemini \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-compass-api-key-here" \
  -d '{
    "messages": [
      {"role": "user", "content": "こんにちは"}
    ],
    "config": {
      "model": "gemini-2.0-flash-exp",
      "memory_search_config": {
        "enabled": true,
        "target": "content",
        "limit": 3,
        "search_type": "normal"
      },
      "gemini_params": {
        "temperature": 0.7
      }
    }
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/chat/gemini",
    headers={
        "Authorization": "Bearer your-compass-api-key-here",
        "Content-Type": "application/json"
    },
    json={
        "messages": [
            {"role": "user", "content": "こんにちは、ありす。"},
            {"role": "model", "content": "こんにちは、ご主人様！"},
            {"role": "user", "content": "今日の天気は?"}
        ],
        "config": {
            "model": "gemini-2.0-flash-exp",
            "memory_search_config": {
                "enabled": True,
                "target": "content",
                "limit": 3,
                "search_type": "normal"
            },
            "gemini_params": {
                "temperature": 0.7,
                "max_output_tokens": 1024
            }
        }
    }
)

result = response.json()
print(result['response']['content'])
```

---

## CORS Configuration

The API is configured to allow all origins in development:

```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
allow_headers=["*"]
```

**⚠️ Security Note:** Update CORS settings before deploying to production.

## Vector Search Details

### Embedding Model
- **Model:** `intfloat/multilingual-e5-large`
- **Prefix:** Queries are prefixed with `"query: "` for optimal performance
- **Normalization:** L2 normalization applied to all vectors
- **Device:** Automatically uses CUDA if available, otherwise CPU

### Search Metrics
- **Distance Metric:** L2 (Euclidean distance)
- **Vector Columns:**
  - `vector_summary`: Embeddings of AI-generated summaries
  - `vector_content`: Embeddings of original content

### Search Process
1. Query text is embedded using the same model
2. Vector similarity search is performed on selected column
3. Results are ranked by L2 distance
4. Top N results are returned
5. (Optional) Results are compressed using Ollama

## AI Summarization

### Ollama Configuration
- **API URL:** `http://localhost:11434/api/generate`
- **Model:** `gemma3:4b` (configurable)
- **Input Limit:** 4000 characters per request

### Chunked Summarization
For text exceeding 4000 characters:
1. Text is split into 4000-character chunks
2. Each chunk is summarized individually
3. Chunk summaries are combined
4. Final summary is generated from combined text

### Prompt Template
```
以下のテキストの要点を、客観的な事実として100-1000文字で簡潔な日本語で要約してください。
---
{text}
---
要約:
```

## Error Handling

**As of v2.6.0 (Phase 5)**, the API implements comprehensive error handling with custom exceptions and global handlers.

### HTTP Status Codes

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful request
- `204 No Content`: Successful deletion
- `400 Bad Request`: Invalid input parameters (client errors)
  - `InvalidQueryError`: Invalid search query
  - `DataValidationError`: Data validation failed
  - `TokenLimitExceededError`: Token count exceeded limit
- `401 Unauthorized`: Authentication errors
  - Missing or invalid authentication
  - `GeminiAuthError`: Gemini API authentication failed
- `404 Not Found`: Resource not found
  - `RecordNotFoundError`: Record with specified ID not found
- `500 Internal Server Error`: Server-side processing errors
  - `DatabaseConnectionError`: Database connection failed
  - `DatabaseOperationError`: Database operation failed
  - `TableNotFoundError`: Database table not found
  - `EmbeddingGenerationError`: Embedding generation failed
  - `ModelLoadError`: Model loading failed
  - `ConfigurationError`: Configuration error
  - `FileLoadError`: File loading error
  - `SearchError`: Search processing error
  - `MemoryUpdateError`: Memory update failed
  - `MemoryDeleteError`: Memory deletion failed
- `502 Bad Gateway`: External API errors
  - `OllamaAPIError`: Ollama API call failed
  - `GeminiAPIError`: Gemini API call failed
- `503 Service Unavailable`: External service unavailable
  - `OllamaConnectionError`: Cannot connect to Ollama

### Error Response Format (Phase 5+)

**Consistent Error Response:**
```json
{
  "error": "RecordNotFoundError",
  "detail": "ID 'abc-123' のレコードが見つかりませんでした",
  "status_code": 404
}
```

**Fields:**
- `error`: Exception class name (identifies error type)
- `detail`: Human-readable error message (in Japanese)
- `status_code`: HTTP status code

**Authentication Error Example:**
```json
{
  "error": "HTTPException",
  "detail": "Authorization header is missing or invalid.",
  "status_code": 401
}
```

**Database Error Example:**
```json
{
  "error": "TableNotFoundError",
  "detail": "テーブル 'memory_atoms' が見つかりません。プロジェクトルートで 'python scripts/main_pipeline.py' を先に実行してください。",
  "status_code": 500
}
```

**Unexpected Error Response:**
For any unexpected errors, a safe generic response is returned:
```json
{
  "error": "InternalServerError",
  "detail": "サーバー内部エラーが発生しました。管理者に連絡してください。",
  "status_code": 500
}
```

### Error Handling Architecture (Phase 5)

The API uses a layered error handling approach:

1. **Custom Exceptions** (`api/exceptions.py`): 18 domain-specific exception classes
2. **Global Exception Handlers** (`api/main.py`): Catch and format all exceptions
3. **Service Layer**: Raises specific exceptions for different error conditions
4. **Routers**: Let exceptions bubble up (no try-catch blocks needed)

**Benefits:**
- Consistent error responses across all endpoints
- Detailed error information for debugging
- Safe error messages for users (no internal details exposed)
- Easy to add new error types

## Performance Considerations

### Database Operations
- **Search:** O(n) vector similarity search (optimized by LanceDB)
- **List:** Requires full table scan for filtering
- **Update:** Delete + Add operation (two database operations)
- **Delete:** Single delete operation

### Optimization Tips
1. Use `summary` search target for faster results (summaries are shorter)
2. Limit result count to reduce embedding computation
3. Disable compression unless needed (saves Ollama API calls)
4. Use date filtering to reduce dataset size

### Caching
- Model and tokenizer are loaded once at startup
- No response caching implemented (future enhancement)

## Database Schema

LanceDB table: `memory_atoms`

```python
schema = pa.schema([
    pa.field("id", pa.string()),
    pa.field("content", pa.string()),
    pa.field("summary", pa.string()),
    pa.field("timestamp", pa.string()),
    pa.field("source_type", pa.string()),
    pa.field("source_name", pa.string()),
    pa.field("metadata", pa.struct([
        pa.field("speakers", pa.list_(pa.string()))
    ])),
    pa.field("vector_content", pa.list_(pa.float32(), list_size=1024)),
    pa.field("vector_summary", pa.list_(pa.float32(), list_size=1024)),
    pa.field("entities", pa.list_(
        pa.struct([
            pa.field("name", pa.string()),
            pa.field("type", pa.string())
        ])
    )),
    pa.field("relationships", pa.list_(
        pa.struct([
            pa.field("target_id", pa.string()),
            pa.field("type", pa.string()),
            pa.field("weight", pa.float32())
        ])
    ))
])
```

## Client Examples

### Python
```python
import requests

# Set up headers with API key
headers = {
    "Authorization": "Bearer your-compass-api-key-here",
    "Content-Type": "application/json"
}

# Search
response = requests.post(
    "http://localhost:8000/search",
    headers=headers,
    json={
        "text": "検索クエリ",
        "config": {"target": "summary", "limit": 5}
    }
)
results = response.json()

# List with pagination
response = requests.post(
    "http://localhost:8000/list",
    headers=headers,
    json={"limit": 50, "offset": 100}
)
data = response.json()

# Update
response = requests.put(
    f"http://localhost:8000/update/{record_id}",
    headers=headers,
    json={
        "summary": "新しい要約",
        "content": "新しい内容",
        "timestamp": "2025-10-08T12:00:00",
        "speakers": ["ありす"]
    }
)

# Delete
response = requests.delete(
    f"http://localhost:8000/delete/{record_id}",
    headers=headers
)
```

### JavaScript/TypeScript
```typescript
// Set up headers with API key
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-compass-api-key-here'
}

// Search
const searchResults = await fetch('http://localhost:8000/search', {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({
    text: '検索クエリ',
    config: { target: 'summary', limit: 5 }
  })
}).then(res => res.json())

// List
const listResponse = await fetch('http://localhost:8000/list', {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({ limit: 50, offset: 0 })
}).then(res => res.json())

// Update
await fetch(`http://localhost:8000/update/${recordId}`, {
  method: 'PUT',
  headers: headers,
  body: JSON.stringify({
    summary: '新しい要約',
    content: '新しい内容',
    timestamp: '2025-10-08T12:00:00',
    speakers: ['ありす']
  })
})

// Delete
await fetch(`http://localhost:8000/delete/${recordId}`, {
  method: 'DELETE',
  headers: { 'Authorization': 'Bearer your-compass-api-key-here' }
})
```

## Development

### Running the API Server

**Using batch file:**
```bash
start_api.bat
```

**Manual start:**
```bash
conda activate compass-env
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

The API uses environment variables for configuration. Create a `.env` file in the project root:

```env
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434

# Google Gemini API Configuration
GOOGLE_API_KEY=your-google-api-key-here
COMPASS_API_KEY=your-compass-api-key-here

# File Paths
SYSTEM_PROMPT_PATH=data/prompts/system_prompt.txt
LONG_TERM_MEMORY_PATH=data/prompts/long_term_memory.txt
```

**Environment Variables:**
- `OLLAMA_HOST`: Ollama API endpoint (default: `http://localhost:11434`)
- `GOOGLE_API_KEY`: Google Gemini API key (required for `/chat/gemini` endpoint)
- `COMPASS_API_KEY`: **[Required v2.2.1+]** API key for authenticating all client requests (Bearer token authentication)
- `SYSTEM_PROMPT_PATH`: Path to system prompt file (default: `data/prompts/system_prompt.txt`)
- `LONG_TERM_MEMORY_PATH`: Path to long-term memory file (default: `data/prompts/long_term_memory.txt`)

**Note:** If `COMPASS_API_KEY` is not set, authentication is skipped (development mode only). Always set this in production.

**Note:** The Ollama model (`gemma3:4b`) is currently hardcoded in `api/main.py` line 49.

### Testing

Use the interactive API docs for testing:
1. Navigate to http://localhost:8000/docs
2. Click "Try it out" on any endpoint
3. Fill in parameters and execute

Or use command-line tools:
```bash
# Test search (requires authentication)
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-compass-api-key-here" \
  -d '{"text": "test"}'

# Test list (requires authentication)
curl -X POST http://localhost:8000/list \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-compass-api-key-here" \
  -d '{"limit": 10}'
```

## Deployment Considerations

### Production Checklist
- [ ] **Set `COMPASS_API_KEY` in production environment** (required for authentication)
- [ ] Update CORS settings to restrict origins
- [ ] Secure API keys (use secrets management service)
- [ ] Rotate `COMPASS_API_KEY` regularly
- [ ] Implement rate limiting (especially for `/chat/gemini`)
- [ ] Add request logging with API key masking
- [ ] Set up response caching
- [ ] Configure all environment variables securely
- [ ] Use production ASGI server (Gunicorn + Uvicorn)
- [ ] Set up SSL/TLS
- [ ] Monitor API performance and token usage
- [ ] Implement backup strategy for LanceDB
- [ ] Set up alerts for API errors and authentication failures (401 errors)
- [ ] Review and sanitize conversation logs in `data/dialog/`
- [ ] Test all endpoints with authentication to ensure proper access control
- [ ] Document API key distribution and management procedures

### Scaling
- Consider using a distributed vector database for large datasets
- Implement connection pooling for database access
- Add Redis for caching search results
- Use load balancing for multiple API instances
- Optimize embedding computation (batch processing, GPU)
