# 📥 Import Service

## Service Overview

**Domain**: External content integration and synchronization  
**Core Purpose**: Import and synchronize content from external sources with data transformation  
**Service Type**: Integration Service  
**Dependencies**: Content Management Service, Media Processing Service, User Management Service, Notification Service

---

## 🎯 Functional Responsibilities

### **Primary Functions**
```
├── YouTube API integration and content import
├── RSS feed processing and monitoring
├── External API connectors and data transformation
├── Scheduled import jobs and automation
├── Data mapping and validation
├── Import conflict resolution
├── Batch processing and error handling
└── Import analytics and monitoring
```

### **Secondary Functions**
```
├── Custom data source integration
├── Import configuration management
├── Data quality validation and cleanup
├── Duplicate detection and merging
├── Import history and auditing
├── Performance optimization and caching
├── Error recovery and retry mechanisms
└── Import scheduling and orchestration
```

---

## 🔧 Technical Architecture

### **Tech Stack Specification**
```
Primary Technology:
├── Programming Language: Python 3.11+ (FastAPI + AsyncIO)
├── Task Scheduling: Celery + Redis/SQS
├── HTTP Client: aiohttp (async requests)
├── Data Processing: pandas, BeautifulSoup
└── Database: PostgreSQL (import logs) + Redis (caching)

External Integrations:
├── YouTube Data API v3
├── RSS Feed Parsers: feedparser
├── Generic REST API clients
├── Data Transformation: custom mappers
└── Content Validation: custom validators

Supporting Services:
├── Message Queue: Celery + Redis
├── Cron Jobs: Kubernetes CronJobs
├── Monitoring: Custom metrics + CloudWatch
└── Event Publishing: NATS (import events)
```

### **Service Architecture Diagram**
```
┌─────────────────────────────────────────────────────────────┐
│                      Import Service                        │
├─────────────────┬───────────────────┬───────────────────────┤
│  Import API     │  Processing Engine │   Integration Layer   │
│  (FastAPI)      │     (Celery)      │   (External APIs)     │
├─────────────────┼───────────────────┼───────────────────────┤
│ • Job Control   │ • Data Extraction │ • YouTube API         │
│ • Status Query  │ • Transformation  │ • RSS Feeds           │
│ • Configuration │ • Validation      │ • Custom APIs         │
│ • Monitoring    │ • Conflict Res.   │ • Webhooks            │
└─────────────────┴───────────────────┴───────────────────────┘
         │                 │                       │
         ▼                 ▼                       ▼
┌─────────────────┬───────────────────┬───────────────────────┐
│  Import Config  │    Job Queue      │    Results Store      │
│  (PostgreSQL)   │  (Redis/Celery)   │    (PostgreSQL)       │
└─────────────────┴───────────────────┴───────────────────────┘
```

---

## 🚀 API Specifications

### **Core APIs**

#### **YouTube Channel Import API**
```http
POST /api/v1/import/youtube/channel

Request Body:
{
  "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
  "import_type": "full", // full, incremental, specific
  "options": {
    "include_shorts": true,
    "include_livestreams": false,
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "max_videos": 1000,
    "quality_filter": "high" // any, high, standard
  },
  "mapping_config": {
    "category_mapping": {
      "Education": "تعليمي",
      "Entertainment": "ترفيهي"
    },
    "tag_processing": "auto_translate",
    "description_language": "detect_and_translate"
  },
  "schedule": {
    "type": "recurring", // one_time, recurring
    "cron": "0 6 * * *", // Daily at 6 AM
    "timezone": "Asia/Riyadh"
  }
}

Response (202 Accepted):
{
  "import_job_id": "uuid",
  "status": "pending",
  "estimated_completion": "2024-01-15T16:30:00Z",
  "estimated_items": 450,
  "status_url": "/api/v1/import/jobs/{import_job_id}/status",
  "preview_url": "/api/v1/import/jobs/{import_job_id}/preview"
}
```

#### **RSS Feed Management API**
```http
POST /api/v1/import/rss/feeds

Request Body:
{
  "name": "Al Jazeera Arabic",
  "feed_url": "https://www.aljazeera.net/rss/all.xml",
  "feed_type": "rss", // rss, atom, json
  "check_interval": 900, // seconds (15 minutes)
  "options": {
    "extract_full_content": true,
    "download_media": true,
    "content_filter": {
      "keywords": ["technology", "science"],
      "exclude_keywords": ["sports", "weather"],
      "min_content_length": 100
    }
  },
  "mapping_config": {
    "title_field": "title",
    "content_field": "description",
    "author_field": "author",
    "date_field": "pubDate",
    "category_field": "category"
  },
  "is_active": true
}

Response (201 Created):
{
  "feed_id": "uuid",
  "name": "Al Jazeera Arabic",
  "status": "active",
  "next_check": "2024-01-15T15:15:00Z",
  "items_imported": 0,
  "last_successful_import": null
}
```

#### **Import Job Status API**
```http
GET /api/v1/import/jobs/{jobId}/status

Response (200 OK):
{
  "job_id": "uuid",
  "source_type": "youtube_channel",
  "status": "processing", // pending, processing, completed, failed, cancelled
  "progress": {
    "current_step": "fetching_videos",
    "step_progress": 75,
    "overall_progress": 35,
    "items_processed": 157,
    "items_total": 450,
    "items_successful": 152,
    "items_failed": 5,
    "items_skipped": 0
  },
  "timing": {
    "started_at": "2024-01-15T14:00:00Z",
    "estimated_completion": "2024-01-15T16:30:00Z",
    "last_activity": "2024-01-15T15:45:00Z"
  },
  "current_activity": "Processing video: 'Introduction to Machine Learning'",
  "statistics": {
    "videos_imported": 152,
    "duplicates_detected": 12,
    "errors_encountered": 5,
    "data_processed_mb": 245.7
  },
  "errors": [
    {
      "item_id": "dQw4w9WgXcQ",
      "error": "Video unavailable or private",
      "timestamp": "2024-01-15T15:23:00Z"
    }
  ],
  "next_scheduled_run": "2024-01-16T06:00:00Z"
}
```

#### **Manual Import API**
```http
POST /api/v1/import/manual

Request Body:
{
  "import_type": "json", // json, csv, xml
  "data_format": "content_items",
  "data": [
    {
      "title": "Sample Video Title",
      "description": "Video description in Arabic",
      "url": "https://youtube.com/watch?v=xxxxx",
      "thumbnail_url": "https://img.youtube.com/vi/xxxxx/maxresdefault.jpg",
      "duration": 1200,
      "language": "ar",
      "category": "educational",
      "tags": ["education", "arabic", "tutorial"],
      "published_date": "2024-01-15T12:00:00Z"
    }
  ],
  "options": {
    "validate_urls": true,
    "download_media": false,
    "skip_duplicates": true,
    "auto_categorize": true
  }
}

Response (202 Accepted):
{
  "import_job_id": "uuid",
  "items_queued": 1,
  "validation_results": {
    "valid_items": 1,
    "invalid_items": 0,
    "warnings": []
  }
}
```

---

## 📊 Data Models

### **Database Schema**

#### **ImportSource**
```sql
CREATE TABLE import_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- youtube_channel, youtube_playlist, rss_feed, api_endpoint, manual
    configuration JSONB NOT NULL, -- API keys, endpoints, authentication
    mapping_rules JSONB, -- Field transformation rules
    schedule_config JSONB, -- Cron expressions, intervals
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    next_sync_at TIMESTAMP WITH TIME ZONE,
    total_imports INTEGER DEFAULT 0,
    successful_imports INTEGER DEFAULT 0,
    failed_imports INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_import_sources_type ON import_sources(source_type);
CREATE INDEX idx_import_sources_active ON import_sources(is_active);
CREATE INDEX idx_import_sources_next_sync ON import_sources(next_sync_at);
```

#### **ImportJob**
```sql
CREATE TABLE import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES import_sources(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- full_sync, incremental, manual, scheduled
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed, cancelled, paused
    progress JSONB, -- Current progress information
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_completion TIMESTAMP WITH TIME ZONE,
    
    -- Statistics
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    successful_imports INTEGER DEFAULT 0,
    failed_imports INTEGER DEFAULT 0,
    skipped_items INTEGER DEFAULT 0,
    duplicate_items INTEGER DEFAULT 0,
    
    -- Configuration and results
    import_config JSONB, -- Job-specific configuration
    error_log JSONB, -- Errors and warnings
    summary_results JSONB, -- Final job results
    
    -- Metadata
    triggered_by VARCHAR(50), -- user, schedule, webhook, api
    triggered_by_user UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_import_jobs_status ON import_jobs(status);
CREATE INDEX idx_import_jobs_source ON import_jobs(source_id);
CREATE INDEX idx_import_jobs_created ON import_jobs(created_at DESC);
```

#### **ImportedContent**
```sql
CREATE TABLE imported_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_job_id UUID REFERENCES import_jobs(id) ON DELETE CASCADE,
    source_id UUID REFERENCES import_sources(id),
    
    -- External identifiers
    external_id VARCHAR(255) NOT NULL, -- YouTube video ID, RSS item GUID, etc.
    external_url VARCHAR(1000),
    
    -- Content reference
    content_id UUID, -- References content in Content Management Service
    
    -- Import details
    import_status VARCHAR(20) DEFAULT 'pending', -- pending, processing, success, failed, skipped, duplicate
    import_attempt INTEGER DEFAULT 1,
    
    -- Data tracking
    original_data JSONB, -- Raw data from external source
    transformed_data JSONB, -- Data after transformation rules
    mapping_applied JSONB, -- Which mapping rules were applied
    
    -- Error handling
    error_message TEXT,
    error_code VARCHAR(50),
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    imported_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_imported_content_job ON imported_content(import_job_id);
CREATE INDEX idx_imported_content_external ON imported_content(external_id);
CREATE INDEX idx_imported_content_status ON imported_content(import_status);
CREATE INDEX idx_imported_content_content ON imported_content(content_id);
```

#### **ImportMapping**
```sql
CREATE TABLE import_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL, -- youtube, rss, api
    mapping_name VARCHAR(100) NOT NULL,
    mapping_version INTEGER DEFAULT 1,
    
    -- Field mappings
    field_mappings JSONB NOT NULL, -- Source field to target field mappings
    transformation_rules JSONB, -- Data transformation functions
    validation_rules JSONB, -- Validation constraints
    default_values JSONB, -- Default values for missing fields
    
    -- Conditional logic
    conditional_mappings JSONB, -- If-then mapping rules
    filter_rules JSONB, -- Content filtering rules
    
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_import_mappings_default ON import_mappings(source_type) 
    WHERE is_default = true;
CREATE INDEX idx_import_mappings_type ON import_mappings(source_type);
```

---

## ⚙️ Import Workflows

### **YouTube Channel Import Workflow**
```python
async def import_youtube_channel(source_config: dict, job_config: dict) -> ImportJob:
    """Complete YouTube channel import workflow"""
    
    # 1. Initialize import job
    job = ImportJob(
        source_id=source_config['source_id'],
        job_type='youtube_channel',
        status='processing',
        import_config=job_config
    )
    await db.save(job)
    
    try:
        # 2. Authenticate with YouTube API
        youtube_client = await get_youtube_client(source_config['api_key'])
        
        # 3. Fetch channel information
        channel_info = await youtube_client.channels().list(
            part='snippet,statistics,contentDetails',
            id=job_config['channel_id']
        )
        
        if not channel_info['items']:
            raise ImportError(f"Channel {job_config['channel_id']} not found")
        
        channel = channel_info['items'][0]
        uploads_playlist = channel['contentDetails']['relatedPlaylists']['uploads']
        
        # 4. Get all videos from uploads playlist
        videos = []
        next_page_token = None
        
        while True:
            playlist_response = await youtube_client.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist,
                maxResults=50,
                pageToken=next_page_token
            )
            
            videos.extend(playlist_response['items'])
            next_page_token = playlist_response.get('nextPageToken')
            
            # Update progress
            job.total_items = len(videos)
            await update_job_progress(job)
            
            if not next_page_token:
                break
        
        # 5. Filter videos based on criteria
        filtered_videos = await filter_videos(videos, job_config.get('options', {}))
        job.total_items = len(filtered_videos)
        
        # 6. Process videos in batches
        batch_size = 10
        for i in range(0, len(filtered_videos), batch_size):
            batch = filtered_videos[i:i + batch_size]
            
            # Get detailed video information
            video_ids = [item['contentDetails']['videoId'] for item in batch]
            video_details = await youtube_client.videos().list(
                part='snippet,statistics,contentDetails,status',
                id=','.join(video_ids)
            )
            
            # Process each video in parallel
            tasks = []
            for video_data in video_details['items']:
                task = process_youtube_video(job, video_data, source_config)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update statistics
            for result in results:
                if isinstance(result, Exception):
                    job.failed_imports += 1
                else:
                    job.successful_imports += 1
            
            job.processed_items += len(batch)
            await update_job_progress(job)
        
        # 7. Finalize job
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        await db.save(job)
        
        # 8. Send completion notification
        await notify_import_completion(job)
        
        return job
        
    except Exception as e:
        job.status = 'failed'
        job.error_log = {'error': str(e), 'traceback': traceback.format_exc()}
        await db.save(job)
        raise
```

### **RSS Feed Processing Workflow**
```python
async def process_rss_feed(source: ImportSource) -> ImportJob:
    """Process RSS feed and import new items"""
    
    job = ImportJob(
        source_id=source.id,
        job_type='rss_incremental',
        status='processing'
    )
    await db.save(job)
    
    try:
        # 1. Fetch RSS feed
        async with aiohttp.ClientSession() as session:
            async with session.get(source.configuration['feed_url']) as response:
                feed_content = await response.text()
        
        # 2. Parse feed
        feed = feedparser.parse(feed_content)
        
        if feed.bozo:
            raise ImportError(f"Invalid RSS feed: {feed.bozo_exception}")
        
        # 3. Process feed items
        new_items = []
        for entry in feed.entries:
            # Check if item already exists
            external_id = entry.get('id', entry.get('guid', entry.get('link')))
            
            existing = await db.query(ImportedContent).filter(
                ImportedContent.external_id == external_id,
                ImportedContent.source_id == source.id
            ).first()
            
            if existing:
                continue  # Skip already imported items
            
            # Apply content filters
            if await should_skip_content(entry, source.configuration.get('options', {})):
                continue
            
            new_items.append(entry)
        
        job.total_items = len(new_items)
        await db.save(job)
        
        # 4. Import new items
        for i, entry in enumerate(new_items):
            try:
                await import_rss_item(job, entry, source)
                job.successful_imports += 1
            except Exception as e:
                job.failed_imports += 1
                logger.error(f"Failed to import RSS item: {e}")
            
            job.processed_items = i + 1
            await update_job_progress(job)
        
        # 5. Update source last sync time
        source.last_sync_at = datetime.utcnow()
        source.next_sync_at = calculate_next_sync_time(source.schedule_config)
        source.total_imports += job.successful_imports
        source.successful_imports += job.successful_imports
        await db.save(source)
        
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        await db.save(job)
        
        return job
        
    except Exception as e:
        job.status = 'failed'
        job.error_log = {'error': str(e)}
        await db.save(job)
        raise
```

### **Data Transformation Pipeline**
```python
class DataTransformer:
    """Handles data transformation and mapping for imported content"""
    
    def __init__(self, mapping_config: dict):
        self.mapping_config = mapping_config
        self.field_mappings = mapping_config.get('field_mappings', {})
        self.transformation_rules = mapping_config.get('transformation_rules', {})
        self.validation_rules = mapping_config.get('validation_rules', {})
    
    async def transform_data(self, raw_data: dict, source_type: str) -> dict:
        """Transform raw external data to internal format"""
        
        transformed = {}
        
        # 1. Apply field mappings
        for source_field, target_field in self.field_mappings.items():
            if source_field in raw_data:
                transformed[target_field] = raw_data[source_field]
        
        # 2. Apply transformation rules
        for field, rules in self.transformation_rules.items():
            if field in transformed:
                transformed[field] = await self._apply_transformations(
                    transformed[field], rules
                )
        
        # 3. Apply default values for missing fields
        defaults = self.mapping_config.get('default_values', {})
        for field, default_value in defaults.items():
            if field not in transformed:
                transformed[field] = default_value
        
        # 4. Handle special transformations
        if source_type == 'youtube':
            transformed = await self._transform_youtube_data(raw_data, transformed)
        elif source_type == 'rss':
            transformed = await self._transform_rss_data(raw_data, transformed)
        
        # 5. Validate transformed data
        validation_errors = await self._validate_data(transformed)
        if validation_errors:
            raise ValidationError(f"Data validation failed: {validation_errors}")
        
        return transformed
    
    async def _apply_transformations(self, value: any, rules: list) -> any:
        """Apply transformation rules to a field value"""
        
        for rule in rules:
            rule_type = rule['type']
            
            if rule_type == 'string_transform':
                if rule['operation'] == 'uppercase':
                    value = value.upper()
                elif rule['operation'] == 'lowercase':
                    value = value.lower()
                elif rule['operation'] == 'strip':
                    value = value.strip()
                elif rule['operation'] == 'replace':
                    value = value.replace(rule['from'], rule['to'])
            
            elif rule_type == 'date_transform':
                if rule['operation'] == 'parse':
                    value = dateutil.parser.parse(value)
                elif rule['operation'] == 'format':
                    value = value.strftime(rule['format'])
            
            elif rule_type == 'array_transform':
                if rule['operation'] == 'join':
                    value = rule['separator'].join(value)
                elif rule['operation'] == 'split':
                    value = value.split(rule['separator'])
            
            elif rule_type == 'translate':
                if rule['from_language'] != rule['to_language']:
                    value = await translate_text(
                        value, 
                        rule['from_language'], 
                        rule['to_language']
                    )
        
        return value
    
    async def _transform_youtube_data(self, raw_data: dict, transformed: dict) -> dict:
        """Apply YouTube-specific transformations"""
        
        # Extract duration from ISO 8601 format
        if 'duration' in raw_data.get('contentDetails', {}):
            duration_iso = raw_data['contentDetails']['duration']
            transformed['duration_seconds'] = parse_youtube_duration(duration_iso)
        
        # Extract thumbnail URLs
        thumbnails = raw_data.get('snippet', {}).get('thumbnails', {})
        if thumbnails:
            # Prefer high quality thumbnails
            if 'maxres' in thumbnails:
                transformed['thumbnail_url'] = thumbnails['maxres']['url']
            elif 'high' in thumbnails:
                transformed['thumbnail_url'] = thumbnails['high']['url']
            elif 'medium' in thumbnails:
                transformed['thumbnail_url'] = thumbnails['medium']['url']
        
        # Build video URL
        if 'id' in raw_data:
            transformed['source_url'] = f"https://www.youtube.com/watch?v={raw_data['id']}"
        
        # Extract and transform tags
        if 'tags' in raw_data.get('snippet', {}):
            tags = raw_data['snippet']['tags']
            if self.mapping_config.get('translate_tags'):
                translated_tags = []
                for tag in tags:
                    translated_tag = await translate_text(tag, 'auto', 'ar')
                    translated_tags.append(translated_tag)
                transformed['tags'] = translated_tags
            else:
                transformed['tags'] = tags
        
        return transformed
```

---

## 📈 Performance Requirements

### **Import Performance Targets**
```
YouTube Channel Import:
├── Processing speed: 1000+ videos per hour
├── API rate limiting: Respect YouTube API quotas
├── Concurrent processing: 20+ videos simultaneously
├── Error tolerance: <5% failure rate
└── Data accuracy: >95% successful mapping

RSS Feed Processing:
├── Feed processing: Check 100+ feeds every 15 minutes
├── Item processing: <5 seconds per feed item
├── Duplicate detection: <1 second per item check
├── Batch processing: 50+ items per batch
└── Feed validation: <10 seconds for large feeds

Data Transformation:
├── Mapping speed: <1 second per content item
├── Translation speed: <3 seconds per text field
├── Validation speed: <500ms per item
├── Batch transformation: 100+ items per batch
└── Memory efficiency: <100MB per 1000 items

System Performance:
├── API response time: <200ms for status queries
├── Job scheduling: <5 second scheduling accuracy
├── Database queries: <100ms for job status queries
├── Error recovery: <30 seconds for retry operations
└── Monitoring updates: Real-time progress tracking
```

### **Scalability & Reliability**
```
Horizontal Scaling:
├── Stateless worker processes
├── Queue-based job distribution
├── Auto-scaling based on queue depth
├── Independent import source processing
└── Parallel batch processing

Error Handling:
├── Automatic retry with exponential backoff
├── Dead letter queue for failed items
├── Partial import recovery
├── Import resume capability
└── Detailed error logging and alerting

Resource Management:
├── Memory-efficient data processing
├── Connection pooling for external APIs
├── Rate limiting compliance
├── Cache optimization for repeated data
└── Storage cleanup for old import jobs
```

---

## 🔒 Security & Compliance

### **API Security**
```
External API Integration:
├── Secure credential storage (AWS Secrets Manager)
├── API key rotation and management
├── OAuth2 token refresh automation
├── Rate limiting and quota management
└── Request signing and authentication

Data Security:
├── Encrypted data transmission (TLS 1.3)
├── Sensitive data masking in logs
├── Import data encryption at rest
├── Access control for import configurations
└── Audit trail for all import activities
```

### **Content Compliance**
```
Content Validation:
├── Automated content moderation
├── Copyright infringement detection
├── Age-appropriate content classification
├── Cultural sensitivity checks
└── Terms of service compliance

Data Privacy:
├── GDPR compliance for imported data
├── User consent for data processing
├── Right to deletion for imported content
├── Data minimization principles
└── Cross-border data transfer compliance
```

---

## 🔧 Configuration Examples

### **YouTube Import Configuration**
```yaml
# YouTube channel import configuration
youtube_config:
  api_key: "${YOUTUBE_API_KEY}"
  quota_management:
    daily_quota: 1000000
    requests_per_second: 100
    quota_exceeded_action: "pause_and_retry"
  
  default_options:
    include_shorts: true
    include_livestreams: false
    quality_filter: "high"
    max_videos_per_import: 1000
    skip_duplicates: true
  
  field_mappings:
    title: "title"
    description: "description"
    publishedAt: "published_date"
    duration: "duration_seconds"
    tags: "tags"
    channelTitle: "channel_name"
  
  transformation_rules:
    title:
      - type: "string_transform"
        operation: "strip"
      - type: "translate"
        from_language: "auto"
        to_language: "ar"
        condition: "if_not_arabic"
    
    description:
      - type: "string_transform"
        operation: "strip"
      - type: "html_clean"
        remove_tags: ["script", "style"]
```

### **RSS Feed Configuration**
```yaml
# RSS feed processing configuration
rss_config:
  default_check_interval: 900 # 15 minutes
  max_items_per_check: 100
  content_extraction:
    full_content: true
    extract_images: true
    download_media: false
  
  field_mappings:
    title: "title"
    description: "content"
    link: "source_url"
    pubDate: "published_date"
    author: "author_name"
    category: "categories"
  
  content_filters:
    min_content_length: 100
    max_content_length: 50000
    allowed_languages: ["ar", "en"]
    blocked_domains: ["spam.com", "ads.example.com"]
    required_keywords: []
    blocked_keywords: ["advertisement", "sponsored"]
  
  error_handling:
    max_retries: 3
    retry_delay: 300 # 5 minutes
    skip_on_parse_error: true
    alert_on_feed_unavailable: true
```

This comprehensive Import Service specification provides complete technical details for implementing external content integration with robust error handling, data transformation, and scalability features.