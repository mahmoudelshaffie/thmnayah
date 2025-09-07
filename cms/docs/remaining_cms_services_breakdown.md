# 🏗️ CMS Services: Detailed Component Breakdown (Remaining Services)

## Overview

This document provides detailed technical breakdowns for the remaining 7 CMS services after the Content Management Service (CMS Core). Each service includes functional responsibilities, tech stack specifications, API definitions, and implementation details for the thmnayah platform.

---

## 🎬 2. Media Processing Service

### **Domain & Responsibilities**
**Primary Domain**: Media asset management, processing, and optimization
**Core Purpose**: Handle all media-related operations including upload, processing, transcoding, and analysis

### **Functional Responsibilities**
```
├── Media file upload and validation
├── Video transcoding and format conversion
├── Audio processing and optimization
├── Image processing and thumbnail generation
├── Content transcription (Arabic & English)
├── Media metadata extraction
├── Content moderation and safety checks
└── CDN distribution and optimization
```

### **Tech Stack Specification**
```
Primary Technology:
├── Programming Language: Python 3.11+ (FastAPI)
├── Media Processing: FFmpeg, OpenCV, PIL/Pillow
├── Async Processing: Celery + Redis (background tasks)
├── File Storage: Amazon S3 + CloudFront CDN
└── Database: PostgreSQL (metadata) + Redis (processing status)

AWS Media Services:
├── Video Processing: AWS Elemental MediaConvert
├── Transcription: Amazon Transcribe (Arabic/English)
├── Content Analysis: Amazon Rekognition
├── Content Moderation: Amazon Rekognition (unsafe content detection)
└── File Transfer: Amazon S3 Transfer Acceleration

Supporting Infrastructure:
├── Message Queue: Celery + Redis/SQS
├── Monitoring: CloudWatch + Custom metrics
├── Caching: Redis (processing results)
└── Event Publishing: NATS (processing status updates)
```

### **Key APIs**
```
POST /api/v1/media/upload
├── Request: Multipart file upload with metadata
├── Response: Upload job ID and tracking URL
├── Validation: File type, size, format validation

GET /api/v1/media/job/{jobId}/status
├── Request: Job status check
├── Response: Processing status, progress, results
├── Real-time: WebSocket updates available

POST /api/v1/media/transcode
├── Request: Source media URL, target formats
├── Response: Transcoding job ID
├── Async: Background processing with status updates

GET /api/v1/media/{mediaId}/variants
├── Request: Get all processed variants of media
├── Response: Available formats, qualities, URLs
├── CDN: All URLs are CDN-optimized

POST /api/v1/media/analyze
├── Request: Media URL for content analysis
├── Response: Analysis job ID
├── Features: Object detection, content moderation, transcript
```

### **Data Models**
```
MediaAsset:
├── id: UUID
├── original_filename: String
├── content_type: String (video/audio/image)
├── file_size: Integer
├── s3_key: String
├── cdn_url: String
├── upload_status: Enum (pending, processing, completed, failed)
├── metadata: JSON (duration, resolution, codec, etc.)
├── created_at: Timestamp
└── updated_at: Timestamp

MediaVariant:
├── id: UUID
├── media_asset_id: UUID (FK)
├── variant_type: String (thumbnail, low_res, high_res, audio_only)
├── format: String (mp4, webm, jpg, mp3)
├── quality: String (720p, 1080p, etc.)
├── s3_key: String
├── cdn_url: String
├── file_size: Integer
└── processing_status: Enum

TranscriptionJob:
├── id: UUID
├── media_asset_id: UUID (FK)
├── language: String (ar, en)
├── status: Enum (pending, processing, completed, failed)
├── transcript_text: Text
├── confidence_score: Float
├── timestamps: JSON
└── created_at: Timestamp
```

### **Processing Workflows**
```
Video Upload Workflow:
1. File Upload → S3 (with progress tracking)
2. Metadata Extraction → Database storage
3. Thumbnail Generation → Multiple sizes
4. Video Transcoding → Multiple formats/qualities
5. Content Analysis → Safety and object detection
6. CDN Distribution → Global availability
7. Notification → Content Management Service

Audio Processing Workflow:
1. Audio Upload → S3 storage
2. Format Conversion → Multiple formats (MP3, AAC)
3. Transcription → Arabic/English text
4. Audio Analysis → Content classification
5. Optimization → Compression and quality
6. CDN Distribution → Fast delivery

Image Processing Workflow:
1. Image Upload → S3 storage
2. Format Conversion → WebP, JPEG optimization
3. Thumbnail Generation → Multiple sizes
4. Content Moderation → Safety checks
5. Metadata Extraction → EXIF data
6. CDN Distribution → Optimized delivery
```

### **Performance Requirements**
- File upload: Support up to 5GB files with resume capability
- Transcoding time: <2x real-time for video processing
- Thumbnail generation: <30 seconds for any video
- Content analysis: <5 minutes for 1-hour video
- CDN propagation: <60 seconds globally

---

## 📥 3. Import Service

### **Domain & Responsibilities**
**Primary Domain**: External content integration and synchronization
**Core Purpose**: Import and synchronize content from external sources with data transformation

### **Functional Responsibilities**
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

### **Key APIs**
```
POST /api/v1/import/youtube/channel
├── Request: YouTube channel ID, import configuration
├── Response: Import job ID and schedule
├── Features: Full/incremental sync options

POST /api/v1/import/rss/feed
├── Request: RSS feed URL, parsing rules
├── Response: Feed subscription ID
├── Automation: Periodic feed checking

GET /api/v1/import/jobs
├── Request: Filter by status, source, date range
├── Response: Paginated import job list
├── Analytics: Success rates, processing times

GET /api/v1/import/jobs/{jobId}/status
├── Request: Job status and progress check
├── Response: Processing status, imported items, errors
├── Real-time: Live progress updates

POST /api/v1/import/manual
├── Request: Manual data import (JSON/CSV)
├── Response: Import job ID
├── Validation: Schema validation, duplicate detection

PUT /api/v1/import/mapping/{sourceType}
├── Request: Data mapping configuration
├── Response: Updated mapping rules
├── Features: Field mapping, transformation rules
```

### **Data Models**
```
ImportSource:
├── id: UUID
├── name: String
├── source_type: Enum (youtube, rss, api, manual)
├── configuration: JSON (API keys, endpoints, rules)
├── mapping_rules: JSON (field transformations)
├── schedule: Cron expression
├── is_active: Boolean
├── last_sync: Timestamp
└── created_at: Timestamp

ImportJob:
├── id: UUID
├── source_id: UUID (FK)
├── job_type: Enum (full_sync, incremental, manual)
├── status: Enum (pending, running, completed, failed, paused)
├── started_at: Timestamp
├── completed_at: Timestamp
├── total_items: Integer
├── processed_items: Integer
├── successful_imports: Integer
├── failed_imports: Integer
├── error_log: JSON
└── metadata: JSON

ImportedContent:
├── id: UUID
├── import_job_id: UUID (FK)
├── external_id: String (original source ID)
├── content_id: UUID (FK to content management)
├── import_status: Enum (success, failed, skipped)
├── original_data: JSON
├── transformed_data: JSON
├── error_message: Text
└── imported_at: Timestamp
```

### **Import Workflows**
```
YouTube Channel Import:
1. Channel Discovery → Fetch channel metadata
2. Video Enumeration → Get all videos/playlists
3. Content Analysis → Extract metadata, descriptions
4. Data Transformation → Map to internal schema
5. Duplicate Detection → Check existing content
6. Content Creation → Create/update content records
7. Media Processing → Queue video processing
8. Status Reporting → Update import progress

RSS Feed Processing:
1. Feed Fetching → Download and parse RSS/Atom
2. Content Extraction → Parse items and metadata
3. Change Detection → Compare with last sync
4. Content Mapping → Transform to internal format
5. Media Discovery → Extract associated media files
6. Content Import → Create content records
7. Media Import → Queue media processing
8. Feed Update → Update last processed timestamp

Generic API Import:
1. API Discovery → Fetch available endpoints
2. Data Retrieval → Paginated content fetching
3. Schema Validation → Validate against mapping rules
4. Data Transformation → Apply mapping transformations
5. Conflict Resolution → Handle duplicates and updates
6. Batch Processing → Process in configurable batches
7. Error Handling → Retry failed items with backoff
8. Completion Notification → Notify stakeholders
```

### **Performance Requirements**
- YouTube import: Process 1000+ videos per hour
- RSS processing: Check 100+ feeds every 15 minutes
- Data transformation: <1 second per content item
- Error recovery: Automatic retry with exponential backoff
- Import reliability: >95% success rate for valid content

---

## 📚 4. Content Organization Service

### **Domain & Responsibilities**
**Primary Domain**: Content taxonomy, relationships, and organizational structure
**Core Purpose**: Manage content hierarchies, series, categories, and content discovery optimization

### **Functional Responsibilities**
```
├── Series and episode management
├── Content categorization and tagging
├── Content relationships and recommendations
├── Featured content promotion and scheduling
├── Content taxonomy management
├── Publication workflow and scheduling
├── Content collection and playlist management
└── Content discovery optimization
```

### **Tech Stack Specification**
```
Primary Technology:
├── Programming Language: Python 3.11+ (FastAPI)
├── Graph Database: Neo4j (content relationships)
├── Search Engine: Elasticsearch (categorization)
├── Cache Layer: Redis (taxonomy cache)
└── Database: PostgreSQL (series, categories)

Algorithm Libraries:
├── Content Similarity: scikit-learn
├── Recommendation Engine: Surprise/LightFM
├── Graph Analytics: NetworkX
├── Text Processing: spaCy (Arabic/English)
└── ML Pipeline: pandas + numpy

Supporting Infrastructure:
├── Task Queue: Celery + Redis
├── Event Bus: NATS (content organization events)
├── Monitoring: Custom metrics + Prometheus
└── Caching: Redis (relationship cache)
```

### **Key APIs**
```
POST /api/v1/series
├── Request: Series metadata, content list
├── Response: Created series with episode ordering
├── Features: Automatic episode numbering

GET /api/v1/series/{seriesId}/episodes
├── Request: Series ID with pagination
├── Response: Ordered episode list with metadata
├── Sorting: Episode number, air date, custom order

POST /api/v1/content/{contentId}/relationships
├── Request: Content ID, related content, relationship type
├── Response: Created relationship
├── Types: similar, sequel, part_of, references

GET /api/v1/content/{contentId}/recommendations
├── Request: Content ID, recommendation count
├── Response: Recommended content with similarity scores
├── Algorithm: Content-based + collaborative filtering

PUT /api/v1/content/{contentId}/featured
├── Request: Featured status, promotion period
├── Response: Updated featured content
├── Scheduling: Time-based promotion periods

GET /api/v1/categories/tree
├── Request: Category hierarchy request
├── Response: Nested category structure
├── Features: Multilingual category names

POST /api/v1/collections
├── Request: Collection metadata, content list
├── Response: Created collection
├── Types: manual_curation, auto_generated, themed
```

### **Data Models**
```
Series:
├── id: UUID
├── title: JSON (multilingual)
├── description: JSON (multilingual)
├── category_id: UUID (FK)
├── total_episodes: Integer
├── status: Enum (ongoing, completed, hiatus)
├── created_by: UUID (FK to users)
├── created_at: Timestamp
├── updated_at: Timestamp
└── metadata: JSON (tags, themes, etc.)

Episode:
├── id: UUID
├── series_id: UUID (FK)
├── content_id: UUID (FK to content management)
├── episode_number: Integer
├── season_number: Integer
├── title: JSON (multilingual)
├── air_date: Date
├── is_special: Boolean
├── sort_order: Integer
└── episode_metadata: JSON

ContentRelationship:
├── id: UUID
├── source_content_id: UUID (FK)
├── target_content_id: UUID (FK)
├── relationship_type: Enum (similar, sequel, prequel, spin_off)
├── strength_score: Float (0.0-1.0)
├── created_by: UUID (system/user)
├── is_verified: Boolean
└── created_at: Timestamp

Category:
├── id: UUID
├── name: JSON (multilingual)
├── slug: String
├── parent_id: UUID (FK, self-reference)
├── description: JSON (multilingual)
├── sort_order: Integer
├── is_active: Boolean
├── icon_url: String
└── metadata: JSON

FeaturedContent:
├── id: UUID
├── content_id: UUID (FK)
├── featured_type: Enum (hero, trending, editor_choice)
├── promotion_start: Timestamp
├── promotion_end: Timestamp
├── priority: Integer
├── created_by: UUID (FK)
├── is_active: Boolean
└── view_count: Integer (tracking)
```

### **Organization Workflows**
```
Series Creation Workflow:
1. Series Metadata → Validate and create series
2. Episode Assignment → Link existing content as episodes
3. Episode Ordering → Automatic/manual episode numbering
4. Relationship Detection → Find related content automatically
5. Category Assignment → AI-powered categorization
6. Search Indexing → Update search indices
7. Recommendation Update → Refresh recommendation models

Content Categorization Workflow:
1. Content Analysis → Extract topics, themes, keywords
2. Category Suggestion → ML-powered category recommendations
3. Manual Review → Editor approval/modification
4. Taxonomy Update → Update category relationships
5. Search Optimization → Update search metadata
6. Similar Content → Find related content in same categories

Featured Content Management:
1. Content Selection → Editor selection or algorithm-based
2. Promotion Scheduling → Time-based promotion periods
3. Performance Tracking → Monitor engagement metrics
4. Dynamic Adjustment → Adjust based on performance
5. Rotation Management → Automatic content rotation
6. Archive Management → Move expired promotions

Recommendation Generation:
1. Content Analysis → Extract content features
2. User Behavior → Analyze user interaction patterns
3. Similarity Calculation → Compute content similarity
4. Collaborative Filtering → Find users with similar tastes
5. Hybrid Approach → Combine content + collaborative signals
6. Ranking Optimization → Rank recommendations by relevance
7. Real-time Updates → Update recommendations based on new data
```

### **Performance Requirements**
- Series episode retrieval: <100ms for 1000+ episodes
- Content recommendations: <200ms for 20 recommendations
- Category tree: <50ms for full hierarchy (cached)
- Relationship queries: <150ms for content relationships
- Featured content updates: Real-time propagation <30 seconds

---

## 👤 5. User Management Service

### **Domain & Responsibilities**
**Primary Domain**: Identity management, authentication, authorization, and user profiles
**Core Purpose**: Secure user authentication, role-based access control, and user profile management

### **Functional Responsibilities**
```
├── User authentication and session management
├── Role-based access control (RBAC)
├── User profile management and preferences
├── Team and organization management
├── Single Sign-On (SSO) integration
├── Multi-factor authentication (MFA)
├── User activity auditing and logging
└── Account lifecycle management
```

### **Tech Stack Specification**
```
Primary Technology:
├── Programming Language: Python 3.11+ (FastAPI)
├── Authentication: Keycloak (SSO/Identity Provider)
├── Session Store: Redis Cluster
├── Database: PostgreSQL (user data)
└── Security: bcrypt, PyJWT, cryptography

Identity & Security:
├── SSO Integration: Keycloak + OAuth2/OIDC
├── Multi-Factor Auth: TOTP (Google Authenticator)
├── JWT Management: Custom token validation
├── Password Security: bcrypt + salt
└── Rate Limiting: Redis-based request throttling

Supporting Infrastructure:
├── Cache: Redis (sessions, permissions)
├── Event Bus: NATS (user events)
├── Monitoring: Security event monitoring
└── Audit: PostgreSQL (audit trail)
```

### **Key APIs**
```
POST /api/v1/auth/login
├── Request: Username/email, password, MFA token (optional)
├── Response: JWT access token, refresh token, user profile
├── Security: Rate limiting, brute force protection

POST /api/v1/auth/refresh
├── Request: Refresh token
├── Response: New access token
├── Validation: Token expiry, blacklist check

POST /api/v1/users
├── Request: User creation data, role assignment
├── Response: Created user profile
├── Authorization: Admin role required

GET /api/v1/users/{userId}/profile
├── Request: User ID (self or admin)
├── Response: User profile data
├── Privacy: Filtered based on requester permissions

PUT /api/v1/users/{userId}/roles
├── Request: Role assignments/removals
├── Response: Updated user roles
├── Authorization: Role management permissions required

GET /api/v1/roles/permissions
├── Request: Role-based permission query
├── Response: Available permissions by role
├── Caching: Heavily cached for performance

POST /api/v1/users/{userId}/mfa/enable
├── Request: MFA setup (TOTP secret)
├── Response: MFA configuration
├── Security: Requires current password confirmation
```

### **Data Models**
```
User:
├── id: UUID
├── username: String (unique)
├── email: String (unique)
├── password_hash: String (bcrypt)
├── first_name: String
├── last_name: String
├── is_active: Boolean
├── is_verified: Boolean
├── last_login: Timestamp
├── created_at: Timestamp
├── updated_at: Timestamp
├── preferences: JSON
└── metadata: JSON

Role:
├── id: UUID
├── name: String (unique)
├── description: String
├── is_system_role: Boolean
├── permissions: Array[String]
├── created_at: Timestamp
└── updated_at: Timestamp

UserRole:
├── user_id: UUID (FK)
├── role_id: UUID (FK)
├── assigned_by: UUID (FK)
├── assigned_at: Timestamp
├── expires_at: Timestamp (optional)
└── is_active: Boolean

UserSession:
├── session_id: UUID
├── user_id: UUID (FK)
├── access_token: String (hashed)
├── refresh_token: String (hashed)
├── ip_address: String
├── user_agent: String
├── created_at: Timestamp
├── expires_at: Timestamp
└── is_active: Boolean

UserActivity:
├── id: UUID
├── user_id: UUID (FK)
├── action: String
├── resource: String
├── resource_id: String
├── ip_address: String
├── user_agent: String
├── timestamp: Timestamp
└── metadata: JSON
```

### **Authentication & Authorization Workflows**
```
User Registration Workflow:
1. Registration Request → Validate user data
2. Email Verification → Send verification email
3. Account Activation → Confirm email and activate
4. Profile Setup → Complete user profile
5. Role Assignment → Assign default role
6. Welcome Notification → Send welcome message

Login Workflow:
1. Credentials Validation → Check username/password
2. MFA Challenge → If enabled, request MFA token
3. Session Creation → Generate JWT tokens
4. Permission Loading → Load user roles/permissions
5. Activity Logging → Log successful login
6. Session Tracking → Store session in Redis

Authorization Workflow:
1. Token Validation → Verify JWT signature and expiry
2. User Lookup → Get user from token claims
3. Permission Check → Validate action against user roles
4. Resource Access → Grant/deny based on permissions
5. Activity Logging → Log access attempt
6. Cache Update → Update permission cache if needed

Role Management Workflow:
1. Role Definition → Create role with permissions
2. Permission Assignment → Assign specific permissions
3. User Assignment → Assign role to users
4. Inheritance Check → Validate role hierarchy
5. Cache Invalidation → Clear permission caches
6. Audit Logging → Log role changes
```

### **Security Requirements**
- Password policy: Minimum 8 characters, complexity requirements
- Session timeout: 24 hours for web, 7 days for mobile
- Rate limiting: 5 failed login attempts per IP per minute
- MFA support: TOTP-based multi-factor authentication
- Audit trail: Complete log of all authentication events

---

## 📊 6. Analytics & Reporting Service

### **Domain & Responsibilities**
**Primary Domain**: Business intelligence, performance analytics, and reporting
**Core Purpose**: Collect, process, and analyze platform data to provide actionable insights

### **Functional Responsibilities**
```
├── Content performance analytics and metrics
├── User engagement tracking and analysis
├── System health monitoring and reporting
├── Import job analytics and success tracking
├── Search analytics and optimization insights
├── Custom dashboard creation and management
├── Automated report generation and delivery
└── Data export and integration capabilities
```

### **Tech Stack Specification**
```
Primary Technology:
├── Programming Language: Python 3.11+ (FastAPI)
├── Analytics Engine: Apache Spark/pandas
├── Time Series DB: InfluxDB + Grafana
├── Data Warehouse: PostgreSQL + Clickhouse
└── Visualization: Grafana + Custom dashboards

Data Processing:
├── Stream Processing: Apache Kafka/Kinesis
├── Batch Processing: Apache Airflow
├── ETL Pipeline: Apache Spark + pandas
├── Data Storage: S3 Data Lake + Parquet
└── Real-time Analytics: Redis Streams

Business Intelligence:
├── Dashboard: Grafana + Custom React components
├── Report Generation: Pandas + Matplotlib
├── Data Export: CSV, Excel, JSON, PDF
├── Alerting: Custom alerts + Slack/email
└── Scheduling: Celery + cron jobs
```

### **Key APIs**
```
GET /api/v1/analytics/content/{contentId}/metrics
├── Request: Content ID, date range, metrics type
├── Response: Content performance metrics
├── Metrics: Views, engagement, ratings, shares

GET /api/v1/analytics/dashboard/overview
├── Request: Dashboard type, filters, date range
├── Response: Dashboard data with KPIs
├── Real-time: Live metrics with WebSocket updates

POST /api/v1/analytics/reports/generate
├── Request: Report configuration, schedule, recipients
├── Response: Report job ID
├── Formats: PDF, Excel, CSV, JSON

GET /api/v1/analytics/users/engagement
├── Request: User segments, metrics, date range
├── Response: User engagement analytics
├── Segmentation: By role, activity, demographics

GET /api/v1/analytics/search/insights
├── Request: Search query analysis parameters
├── Response: Search performance insights
├── Insights: Popular queries, zero results, trends

GET /api/v1/analytics/system/health
├── Request: System metrics, time range
├── Response: System performance metrics
├── Metrics: Response times, error rates, resource usage

POST /api/v1/analytics/events/track
├── Request: Event data (user action, context)
├── Response: Event tracking confirmation
├── Real-time: Immediate processing and aggregation
```

### **Data Models**
```
ContentMetrics:
├── id: UUID
├── content_id: UUID (FK)
├── date: Date
├── view_count: Integer
├── unique_viewers: Integer
├── average_watch_time: Integer (seconds)
├── completion_rate: Float
├── engagement_score: Float
├── share_count: Integer
├── favorite_count: Integer
├── comment_count: Integer
└── updated_at: Timestamp

UserEngagement:
├── id: UUID
├── user_id: UUID (FK)
├── date: Date
├── session_count: Integer
├── total_session_time: Integer (seconds)
├── page_views: Integer
├── content_interactions: Integer
├── search_queries: Integer
├── downloads: Integer
├── shares: Integer
└── last_activity: Timestamp

SearchAnalytics:
├── id: UUID
├── query_text: String
├── date: Date
├── search_count: Integer
├── result_count: Integer
├── click_through_rate: Float
├── average_position: Float
├── zero_result_rate: Float
├── language: String
└── user_type: Enum (anonymous, registered)

SystemMetrics:
├── id: UUID
├── service_name: String
├── metric_name: String
├── metric_value: Float
├── timestamp: Timestamp
├── tags: JSON
└── metadata: JSON

Report:
├── id: UUID
├── name: String
├── description: Text
├── report_type: Enum (content, user, system, custom)
├── configuration: JSON
├── schedule: Cron expression
├── recipients: Array[String]
├── last_generated: Timestamp
├── is_active: Boolean
├── created_by: UUID (FK)
└── created_at: Timestamp
```

### **Analytics Workflows**
```
Data Collection Workflow:
1. Event Tracking → Capture user interactions
2. Data Validation → Validate and clean incoming data
3. Real-time Processing → Process events immediately
4. Batch Aggregation → Hourly/daily aggregation jobs
5. Data Storage → Store in time-series database
6. Index Update → Update search and query indices

Report Generation Workflow:
1. Schedule Trigger → Cron job or manual trigger
2. Data Extraction → Query relevant data sources
3. Data Processing → Apply filters, aggregations
4. Visualization → Generate charts and graphs
5. Format Generation → Create PDF/Excel/CSV
6. Distribution → Send to recipients
7. Archive → Store generated reports

Dashboard Creation Workflow:
1. Metrics Selection → Choose relevant KPIs
2. Data Source Configuration → Connect to data sources
3. Visualization Setup → Configure charts and widgets
4. Real-time Updates → Set up live data feeds
5. Access Control → Set dashboard permissions
6. Performance Optimization → Cache and optimize queries

Alert Configuration Workflow:
1. Threshold Definition → Set alert conditions
2. Notification Setup → Configure recipients and channels
3. Alert Monitoring → Continuously check conditions
4. Trigger Execution → Send alerts when thresholds met
5. Escalation → Handle repeated or critical alerts
6. Resolution Tracking → Track alert resolution
```

### **Performance Requirements**
- Real-time metrics: <5 second latency for dashboard updates
- Report generation: <2 minutes for standard monthly reports
- Query performance: <3 seconds for complex analytics queries
- Data retention: 2+ years of detailed metrics
- Alert latency: <1 minute from threshold breach to notification

---

## 🔔 7. Notification Service

### **Domain & Responsibilities**
**Primary Domain**: Event-driven notifications and cross-service communication
**Core Purpose**: Handle all types of notifications, alerts, and messaging within the platform

### **Functional Responsibilities**
```
├── Real-time notification delivery
├── Email notification management
├── SMS and push notification support
├── Event-driven messaging between services
├── Notification preferences and subscriptions
├── Notification templates and localization
├── Delivery tracking and analytics
└── Alert escalation and routing
```

### **Tech Stack Specification**
```
Primary Technology:
├── Programming Language: Python 3.11+ (FastAPI)
├── Message Broker: NATS/Apache Kafka
├── Email Service: Amazon SES + custom templates
├── Push Notifications: Firebase Cloud Messaging (FCM)
└── Database: PostgreSQL (templates, preferences)

Real-time Communication:
├── WebSocket Server: FastAPI WebSocket
├── Real-time Updates: Socket.IO
├── Message Queue: Redis Pub/Sub
├── Event Streaming: NATS Streaming
└── Load Balancing: NGINX for WebSocket

Template & Localization:
├── Template Engine: Jinja2
├── Localization: Babel (Arabic/English)
├── HTML Email: MJML templates
├── SMS Templates: Simple text templates
└── Push Templates: JSON structured messages
```

### **Key APIs**
```
POST /api/v1/notifications/send
├── Request: Recipient, message, notification type
├── Response: Notification ID and delivery status
├── Types: email, sms, push, in_app

GET /api/v1/notifications/{userId}/inbox
├── Request: User ID, pagination, filters
├── Response: User's notification inbox
├── Features: Read/unread status, threading

PUT /api/v1/notifications/{notificationId}/read
├── Request: Notification ID, read status
├── Response: Updated notification status
├── Real-time: WebSocket update to user

POST /api/v1/notifications/preferences
├── Request: User ID, notification preferences
├── Response: Updated preferences
├── Granular: Per-type, per-channel preferences

POST /api/v1/notifications/templates
├── Request: Template content, type, language
├── Response: Created template
├── Localization: Multi-language template support

GET /api/v1/notifications/delivery/{notificationId}
├── Request: Notification delivery tracking
├── Response: Delivery status, timestamps, errors
├── Analytics: Open rates, click rates

POST /api/v1/notifications/broadcast
├── Request: Message, recipient criteria, scheduling
├── Response: Broadcast job ID
├── Features: Segmented delivery, A/B testing
```

### **Data Models**
```
Notification:
├── id: UUID
├── recipient_id: UUID (user ID)
├── sender_id: UUID (system/user)
├── notification_type: Enum (info, warning, error, success)
├── channel: Enum (email, sms, push, in_app, webhook)
├── subject: String
├── content: Text
├── template_id: UUID (FK, optional)
├── status: Enum (pending, sent, delivered, failed, read)
├── scheduled_at: Timestamp
├── sent_at: Timestamp
├── delivered_at: Timestamp
├── read_at: Timestamp
├── metadata: JSON
└── created_at: Timestamp

NotificationTemplate:
├── id: UUID
├── name: String
├── template_type: Enum (email, sms, push, in_app)
├── subject_template: String
├── content_template: Text
├── language: String (en, ar)
├── is_active: Boolean
├── version: Integer
├── created_by: UUID (FK)
├── created_at: Timestamp
└── template_data: JSON

NotificationPreference:
├── user_id: UUID (FK)
├── notification_type: String
├── channel: Enum (email, sms, push, in_app)
├── is_enabled: Boolean
├── frequency: Enum (immediate, hourly, daily, weekly)
├── quiet_hours_start: Time
├── quiet_hours_end: Time
└── updated_at: Timestamp

DeliveryLog:
├── id: UUID
├── notification_id: UUID (FK)
├── channel: String
├── status: Enum (queued, sending, delivered, failed, bounced)
├── attempt_count: Integer
├── last_attempt: Timestamp
├── next_retry: Timestamp
├── error_message: Text
├── delivery_metadata: JSON (provider response)
└── updated_at: Timestamp

NotificationEvent:
├── id: UUID
├── event_type: String (content_published, user_registered, etc.)
├── source_service: String
├── payload: JSON
├── processed_at: Timestamp
├── notification_count: Integer
├── status: Enum (pending, processed, failed)
└── created_at: Timestamp
```

### **Notification Workflows**
```
Event-Driven Notification Workflow:
1. Service Event → Publish event to message broker
2. Event Processing → Notification service consumes event
3. Rule Evaluation → Check notification rules and preferences
4. Template Selection → Choose appropriate template
5. Content Generation → Render template with event data
6. Recipient Resolution → Determine notification recipients
7. Channel Selection → Choose delivery channels per user
8. Queue for Delivery → Add to appropriate delivery queues

Email Notification Workflow:
1. Template Rendering → Generate HTML/text email content
2. Localization → Apply user's language preferences
3. Personalization → Insert user-specific content
4. Queue Management → Add to email delivery queue
5. SMTP Delivery → Send via Amazon SES
6. Delivery Tracking → Track opens, clicks, bounces
7. Status Updates → Update notification status
8. Analytics Collection → Collect engagement metrics

Real-time Notification Workflow:
1. Trigger Event → Real-time notification needed
2. User Connection Check → Verify user is online
3. WebSocket Delivery → Send via WebSocket connection
4. Fallback Handling → If offline, queue for later
5. Acknowledgment → Confirm receipt from client
6. Status Update → Mark as delivered/read
7. Persistence → Store for offline viewing

Broadcast Notification Workflow:
1. Campaign Setup → Define broadcast parameters
2. Audience Segmentation → Select target recipients
3. Content Preparation → Prepare messages per segment
4. Schedule Management → Queue for scheduled delivery
5. Batch Processing → Process recipients in batches
6. Rate Limiting → Respect delivery rate limits
7. Progress Tracking → Monitor delivery progress
8. Results Analysis → Analyze campaign performance
```

### **Performance Requirements**
- Real-time delivery: <1 second for WebSocket notifications
- Email delivery: <5 minutes for standard emails
- Template rendering: <100ms for complex templates
- Broadcast campaigns: Support 10K+ recipients per campaign
- Delivery tracking: Real-time status updates with <30 second latency

---

## 🔄 Inter-Service Communication & Integration

### **Service Dependency Matrix**
```
┌─────────────────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│     Service     │ CMS │Media│Imprt│ Org │User │Analyt│Notif│
├─────────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ Content Mgmt    │  -  │  →  │  ←  │  ↔  │  ←  │  →  │  →  │
│ Media Process   │  ←  │  -  │  ←  │  →  │  ←  │  →  │  →  │
│ Import Service  │  →  │  →  │  -  │  →  │  ←  │  →  │  →  │
│ Content Org     │  ↔  │  ←  │  ←  │  -  │  ←  │  →  │  →  │
│ User Management │  →  │  →  │  →  │  →  │  -  │  →  │  →  │
│ Analytics       │  ←  │  ←  │  ←  │  ←  │  ←  │  -  │  ←  │
│ Notifications   │  ←  │  ←  │  ←  │  ←  │  ←  │  ←  │  -  │
└─────────────────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Legend: → Sends data to, ← Receives data from, ↔ Bidirectional
```

### **Event-Driven Communication Patterns**
```
Content Lifecycle Events:
├── content.created → Media Processing, Analytics, Notifications
├── content.updated → Content Organization, Search Indexing
├── content.published → Analytics, Notifications, Discovery Service
├── media.processed → Content Management, Analytics
└── import.completed → Content Organization, Analytics, Notifications

User Activity Events:
├── user.registered → Analytics, Notifications, Content Organization
├── user.login → Analytics, Session Management
├── content.viewed → Analytics, Recommendation Engine
├── search.performed → Analytics, Search Optimization
└── content.shared → Analytics, Social Features

System Events:
├── job.completed → Analytics, Notifications
├── error.occurred → Monitoring, Notifications
├── performance.threshold → Analytics, Alerting
└── scheduled.task → All relevant services
```

---

## 🎯 Implementation Priority & Roadmap

### **Phase 1: Core Services (Months 1-2)**
```
High Priority:
├── User Management Service (Authentication foundation)
├── Media Processing Service (Essential for content)
├── Notification Service (Cross-service communication)
└── Basic Analytics Service (Monitoring)

Dependencies: All services depend on User Management for authentication
```

### **Phase 2: Content Services (Months 3-4)**
```
Medium Priority:
├── Import Service (Content acquisition)
├── Content Organization Service (Content structure)
└── Enhanced Analytics Service (Business insights)

Dependencies: Require Phase 1 services operational
```

### **Phase 3: Optimization (Months 5-6)**
```
Enhancement Priority:
├── Advanced media processing features
├── Intelligent content organization
├── Comprehensive analytics dashboards
└── Advanced notification features

Focus: Performance optimization and advanced features
```

This comprehensive breakdown provides detailed technical specifications for all remaining CMS services, ready for implementation planning and development.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Create detailed breakdown for Media Processing Service", "status": "completed", "activeForm": "Creating detailed breakdown for Media Processing Service"}, {"content": "Create detailed breakdown for Import Service", "status": "completed", "activeForm": "Creating detailed breakdown for Import Service"}, {"content": "Create detailed breakdown for Content Organization Service", "status": "completed", "activeForm": "Creating detailed breakdown for Content Organization Service"}, {"content": "Create detailed breakdown for User Management Service", "status": "completed", "activeForm": "Creating detailed breakdown for User Management Service"}, {"content": "Create detailed breakdown for Analytics & Reporting Service", "status": "completed", "activeForm": "Creating detailed breakdown for Analytics & Reporting Service"}, {"content": "Create detailed breakdown for Notification Service", "status": "completed", "activeForm": "Creating detailed breakdown for Notification Service"}]