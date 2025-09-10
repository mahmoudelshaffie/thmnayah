# Content Management Service - Detailed Architecture & API Design

## Service Overview

The **Content Management Service (CMS)** is the core service responsible for managing video programs, metadata, and content lifecycle. It serves as the central hub for all content-related operations and integrates with other services for media processing, search indexing, and notifications.

## Service Architecture

### **Internal Components**

```
┌─────────────────────────────────────────────────────────────┐
│                Content Management Service                   │
├─────────────────┬───────────────────┬───────────────────────┤
│   API Layer     │   Business Logic  │     Data Layer        │
│                 │                   │                       │
│ • REST Endpoints│ • Content Manager │ • Repository Pattern  │
│ • GraphQL       │ • Validation      │ • PostgreSQL Models  │
│ • Auth Middleware│ • Business Rules  │ • Redis Cache        │
│ • Rate Limiting │ • Event Publishing│ • File System        │
└─────────────────┴───────────────────┴───────────────────────┘
```

### **Component Breakdown**

#### 1. **API Layer**
- **REST Controllers**: Handle HTTP requests/responses
- **GraphQL Resolvers**: Complex query handling
- **Authentication Middleware**: JWT validation, role checking
- **Input Validation**: Request data sanitization
- **Rate Limiting**: API usage throttling
- **Error Handling**: Consistent error responses

#### 2. **Business Logic Layer**
- **Content Manager**: Core business operations
- **Validation Engine**: Content validation rules
- **Workflow Engine**: Content lifecycle management
- **Event Publisher**: Publish events to NATS
- **Permission Handler**: Role-based access control

#### 3. **Data Access Layer**
- **Repository Pattern**: Database abstraction
- **Cache Manager**: Redis caching strategy
- **Transaction Manager**: Database transaction handling
- **Migration Handler**: Schema version management

## Database Schema Design

### **PostgreSQL Tables**

#### **programs** (Main content table)
```sql
CREATE TABLE programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title_en VARCHAR(255) NOT NULL,
    title_ar VARCHAR(255),
    description_en TEXT,
    description_ar TEXT,
    slug VARCHAR(255) UNIQUE NOT NULL,
    
    -- Content metadata
    language VARCHAR(10) NOT NULL DEFAULT 'en', -- 'en', 'ar', 'both'
    category_id UUID REFERENCES categories(id),
    duration_seconds INTEGER,
    
    -- Media references
    thumbnail_url VARCHAR(500),
    video_url VARCHAR(500),
    audio_url VARCHAR(500),
    
    -- External references
    youtube_id VARCHAR(50),
    external_id VARCHAR(100),
    external_source VARCHAR(50), -- 'youtube', 'rss', 'manual'
    
    -- Publication
    publication_status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'published', 'archived'
    published_at TIMESTAMPTZ,
    featured BOOLEAN DEFAULT FALSE,
    featured_order INTEGER,
    
    -- Metadata
    tags TEXT[], -- Array of tags
    keywords TEXT[],
    transcript_en TEXT,
    transcript_ar TEXT,
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    version INTEGER DEFAULT 1,
    
    -- Search optimization
    search_vector_en tsvector,
    search_vector_ar tsvector
);

-- Indexes for performance
CREATE INDEX idx_programs_status ON programs(publication_status);
CREATE INDEX idx_programs_category ON programs(category_id);
CREATE INDEX idx_programs_featured ON programs(featured, featured_order);
CREATE INDEX idx_programs_published ON programs(published_at DESC);
CREATE INDEX idx_programs_search_en ON programs USING GIN(search_vector_en);
CREATE INDEX idx_programs_search_ar ON programs USING GIN(search_vector_ar);
CREATE INDEX idx_programs_tags ON programs USING GIN(tags);
```

#### **categories** (Content categorization)
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_en VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100),
    slug VARCHAR(100) UNIQUE NOT NULL,
    description_en TEXT,
    description_ar TEXT,
    parent_id UUID REFERENCES categories(id),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **program_versions** (Content versioning)
```sql
CREATE TABLE program_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content_snapshot JSONB NOT NULL,
    change_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    UNIQUE(program_id, version_number)
);
```

#### **program_media** (Media asset references)
```sql
CREATE TABLE program_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    media_type VARCHAR(20) NOT NULL, -- 'video', 'audio', 'thumbnail', 'document'
    original_filename VARCHAR(255),
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    duration_seconds INTEGER,
    resolution VARCHAR(20), -- '1080p', '720p', etc.
    is_primary BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **Redis Cache Schema**

```json
{
  "program:{id}": {
    "id": "uuid",
    "title_en": "string",
    "title_ar": "string",
    "description_en": "string",
    "category": "object",
    "ttl": 3600
  },
  "programs:featured": [
    "program_id_1",
    "program_id_2"
  ],
  "programs:category:{category_id}": [
    "program_id_1",
    "program_id_3"
  ]
}
```

## REST API Specifications

### **Base Configuration**
- **Base URL**: `/api/v1/cms`
- **Authentication**: Bearer JWT tokens
- **Content-Type**: `application/json`
- **Rate Limiting**: 1000 requests/hour per user

### **Programs Endpoints**

#### **GET /programs** - List Programs
```http
GET /api/v1/cms/programs?page=1&limit=20&category=podcast&status=published&language=ar

Response: 200 OK
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title_en": "Episode 1: Introduction",
      "title_ar": "الحلقة الأولى: مقدمة",
      "description_en": "Welcome to our podcast series...",
      "description_ar": "مرحباً بكم في سلسلة البودكاست...",
      "slug": "episode-1-introduction",
      "language": "both",
      "category": {
        "id": "cat-uuid",
        "name_en": "Podcast",
        "name_ar": "بودكاست",
        "slug": "podcast"
      },
      "duration_seconds": 3600,
      "thumbnail_url": "https://cdn.thmnayah.com/thumbnails/ep1.jpg",
      "publication_status": "published",
      "published_at": "2025-01-15T10:00:00Z",
      "featured": true,
      "featured_order": 1,
      "tags": ["technology", "AI", "تقنية"],
      "created_at": "2025-01-10T09:00:00Z",
      "updated_at": "2025-01-15T09:45:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  },
  "filters": {
    "available_categories": [...],
    "available_languages": ["en", "ar", "both"],
    "available_statuses": ["draft", "published", "archived"]
  }
}
```

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `category`: Filter by category slug
- `status`: Filter by publication status
- `language`: Filter by language
- `featured`: Filter featured content (true/false)
- `search`: Full-text search query
- `sort`: Sort field (created_at, published_at, title, duration)
- `order`: Sort order (asc, desc)

#### **GET /programs/{id}** - Get Program Details
```http
GET /api/v1/cms/programs/550e8400-e29b-41d4-a716-446655440000

Response: 200 OK
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title_en": "Episode 1: Introduction",
  "title_ar": "الحلقة الأولى: مقدمة",
  "description_en": "Welcome to our podcast series...",
  "description_ar": "مرحباً بكم في سلسلة البودكاست...",
  "slug": "episode-1-introduction",
  "language": "both",
  "category": {...},
  "duration_seconds": 3600,
  "media": [
    {
      "id": "media-uuid-1",
      "type": "video",
      "file_path": "/media/videos/ep1_1080p.mp4",
      "resolution": "1080p",
      "file_size": 536870912,
      "is_primary": true,
      "processing_status": "completed"
    },
    {
      "id": "media-uuid-2", 
      "type": "thumbnail",
      "file_path": "/media/thumbnails/ep1.jpg",
      "is_primary": true
    }
  ],
  "external_references": {
    "youtube_id": "dQw4w9WgXcQ",
    "external_source": "youtube"
  },
  "publication_status": "published",
  "published_at": "2025-01-15T10:00:00Z",
  "featured": true,
  "tags": ["technology", "AI", "تقنية"],
  "keywords": ["artificial intelligence", "الذكاء الاصطناعي"],
  "transcript_en": "Welcome everyone...",
  "transcript_ar": "مرحباً بالجميع...",
  "audit": {
    "created_at": "2025-01-10T09:00:00Z",
    "updated_at": "2025-01-15T09:45:00Z",
    "created_by": "user-uuid",
    "version": 3
  }
}
```

#### **POST /programs** - Create Program
```http
POST /api/v1/cms/programs
Authorization: Bearer {jwt_token}
Content-Type: application/json

Request Body:
{
  "title_en": "New Episode Title",
  "title_ar": "عنوان الحلقة الجديدة",
  "description_en": "Episode description...",
  "description_ar": "وصف الحلقة...",
  "language": "both",
  "category_id": "category-uuid",
  "duration_seconds": 2400,
  "tags": ["business", "entrepreneurship", "ريادة"],
  "keywords": ["startup", "investment"],
  "publication_status": "draft",
  "external_references": {
    "youtube_id": "abc123xyz",
    "external_source": "youtube"
  }
}

Response: 201 Created
{
  "id": "new-program-uuid",
  "title_en": "New Episode Title",
  "slug": "new-episode-title",
  "publication_status": "draft",
  "created_at": "2025-01-26T12:00:00Z",
  "message": "Program created successfully"
}
```

#### **PUT /programs/{id}** - Update Program
```http
PUT /api/v1/cms/programs/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {jwt_token}

Request Body:
{
  "title_en": "Updated Episode Title",
  "description_en": "Updated description...",
  "tags": ["technology", "AI", "machine learning"],
  "publication_status": "published"
}

Response: 200 OK
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title_en": "Updated Episode Title",
  "version": 4,
  "updated_at": "2025-01-26T12:30:00Z",
  "message": "Program updated successfully"
}
```

#### **DELETE /programs/{id}** - Delete Program
```http
DELETE /api/v1/cms/programs/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {jwt_token}

Response: 200 OK
{
  "message": "Program deleted successfully",
  "deleted_at": "2025-01-26T13:00:00Z"
}
```

### **Bulk Operations**

#### **POST /programs/bulk** - Bulk Create/Update
```http
POST /api/v1/cms/programs/bulk
Authorization: Bearer {jwt_token}

Request Body:
{
  "operation": "create", // or "update"
  "programs": [
    {
      "title_en": "Bulk Episode 1",
      "category_id": "category-uuid",
      "language": "en"
    },
    {
      "title_en": "Bulk Episode 2", 
      "category_id": "category-uuid",
      "language": "ar"
    }
  ]
}

Response: 202 Accepted
{
  "job_id": "bulk-job-uuid",
  "status": "processing",
  "message": "Bulk operation started",
  "total_items": 2
}
```

#### **GET /jobs/{job_id}** - Get Bulk Operation Status
```http
GET /api/v1/cms/jobs/bulk-job-uuid

Response: 200 OK
{
  "job_id": "bulk-job-uuid",
  "status": "completed", // "processing", "completed", "failed"
  "progress": {
    "total": 2,
    "completed": 2,
    "failed": 0
  },
  "results": [
    {
      "status": "success",
      "program_id": "new-uuid-1",
      "message": "Program created successfully"
    },
    {
      "status": "success", 
      "program_id": "new-uuid-2",
      "message": "Program created successfully"
    }
  ],
  "started_at": "2025-01-26T14:00:00Z",
  "completed_at": "2025-01-26T14:02:00Z"
}
```

### **Categories Endpoints**

#### **GET /categories** - List Categories
```http
GET /api/v1/cms/categories?parent_id=null

Response: 200 OK
{
  "data": [
    {
      "id": "category-uuid-1",
      "name_en": "Podcast",
      "name_ar": "بودكاست",
      "slug": "podcast",
      "description_en": "Audio content series",
      "description_ar": "سلسلة محتوى صوتي",
      "parent_id": null,
      "children": [
        {
          "id": "subcategory-uuid",
          "name_en": "Technology Podcast",
          "name_ar": "بودكاست تقني"
        }
      ],
      "program_count": 45,
      "is_active": true
    }
  ]
}
```

### **Search Endpoints**

#### **GET /search** - Search Programs
```http
GET /api/v1/cms/search?q=artificial intelligence&language=en&category=technology

Response: 200 OK
{
  "query": "artificial intelligence",
  "results": [
    {
      "id": "program-uuid",
      "title_en": "AI in Healthcare",
      "title_ar": "الذكاء الاصطناعي في الرعاية الصحية",
      "description_en": "Exploring AI applications...",
      "relevance_score": 0.95,
      "highlighted_fields": {
        "title_en": "<mark>Artificial Intelligence</mark> in Healthcare",
        "description_en": "Exploring <mark>AI</mark> applications..."
      }
    }
  ],
  "facets": {
    "categories": [
      {"name": "Technology", "count": 23},
      {"name": "Healthcare", "count": 12}
    ],
    "languages": [
      {"name": "English", "count": 30},
      {"name": "Arabic", "count": 15}
    ]
  },
  "total": 35,
  "took_ms": 45
}
```

## Event Publishing

### **NATS Events Published**

```json
{
  "subject": "content.program.created",
  "data": {
    "program_id": "uuid",
    "title_en": "string",
    "category": "string",
    "created_by": "user_uuid",
    "timestamp": "2025-01-26T15:00:00Z"
  }
}

{
  "subject": "content.program.updated", 
  "data": {
    "program_id": "uuid",
    "changes": ["title_en", "description_ar"],
    "updated_by": "user_uuid",
    "timestamp": "2025-01-26T15:00:00Z"
  }
}

{
  "subject": "content.program.published",
  "data": {
    "program_id": "uuid",
    "published_at": "2025-01-26T15:00:00Z",
    "published_by": "user_uuid"
  }
}
```

## Error Handling

### **Standard Error Response Format**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "title_en",
      "constraint": "Title is required and must be between 5-255 characters"
    },
    "request_id": "req-uuid",
    "timestamp": "2025-01-26T15:00:00Z"
  }
}
```

### **Common Error Codes**
- `VALIDATION_ERROR` (400): Invalid input data
- `UNAUTHORIZED` (401): Invalid or missing authentication
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `CONFLICT` (409): Resource already exists
- `RATE_LIMITED` (429): Too many requests
- `INTERNAL_ERROR` (500): Server error

## Performance Considerations

### **Caching Strategy**
- **Redis Cache**: Hot data (featured programs, categories)
- **TTL Settings**: 1 hour for programs, 24 hours for categories
- **Cache Invalidation**: Event-driven cache updates
- **Cache Warming**: Pre-populate cache during deployments

### **Database Optimization**
- **Connection Pooling**: PostgreSQL connection pool
- **Query Optimization**: Proper indexing, query analysis
- **Pagination**: Cursor-based pagination for large datasets
- **Read Replicas**: Separate read/write database connections

### **Monitoring & Metrics**
- **Response Times**: API endpoint performance
- **Error Rates**: Track error frequency by endpoint
- **Database Performance**: Query execution times
- **Cache Hit Rates**: Redis cache effectiveness

## Next Steps

1. **Implement Service Structure**: FastAPI application setup
2. **Database Migration**: PostgreSQL schema creation
3. **API Implementation**: REST endpoints and business logic
4. **Integration Testing**: End-to-end API tests
5. **Event Publishing**: NATS integration for other services
6. **Monitoring Setup**: Prometheus metrics and health checks