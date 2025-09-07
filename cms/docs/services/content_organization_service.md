# Content Organization Service

## Service Overview

**Responsibility**: Series, episodes, and content relationships management  
**Domain**: Content taxonomy and organization  
**Data**: Series, episodes, content relationships, featured content  
**Users**: Content managers, content editors

## Core Features

### Series and Episode Management
- Series creation and metadata management
- Episode ordering and sequencing
- Season organization for long-running series
- Episode-to-series relationship mapping
- Batch operations for episode management

### Content Categorization and Tagging
- Hierarchical category management
- Multi-language category support (Arabic/English)
- Tag creation and assignment
- Content classification automation
- Category and tag analytics

### Featured Content Promotion
- Featured content selection and scheduling
- Homepage content curation
- Promotional content management
- Featured content rotation strategies
- Performance tracking for featured items

### Content Relationships and Recommendations
- Related content mapping
- Content similarity analysis
- Manual relationship override capabilities
- Recommendation weight configuration
- Cross-content referencing

### Publication Scheduling
- Content publication date management
- Scheduled publishing workflows
- Content embargo handling
- Release window management
- Timezone-aware scheduling

---

## Technical Specifications

### Tech Stack
```yaml
Runtime: Python 3.11+
Framework: FastAPI 0.104+
Database: PostgreSQL 15+
Cache: Redis 7+
Message Queue: NATS 2.10+
Search: OpenSearch 2.11+
Monitoring: Prometheus + Grafana
Testing: pytest, asyncio-compatible
```

### Dependencies
```yaml
Internal Services:
  - Content Management Service (content metadata)
  - Search & Discovery Service (indexing updates)
  - Analytics Service (performance data)
  - Notification Service (scheduling alerts)

External Services:
  - PostgreSQL (relational data)
  - Redis (caching, session data)
  - OpenSearch (search indexing)
  - NATS (event messaging)
```

---

## Data Models

### Series Model
```python
class Series(BaseModel):
    id: str = Field(..., description="Unique series identifier")
    title: Dict[str, str] = Field(..., description="Series title (ar/en)")
    description: Dict[str, str] = Field(..., description="Series description (ar/en)")
    slug: Dict[str, str] = Field(..., description="URL-friendly series slug")
    
    # Organization
    category_id: str = Field(..., description="Primary category")
    tags: List[str] = Field(default=[], description="Associated tags")
    
    # Media
    thumbnail_url: Optional[str] = Field(None, description="Series thumbnail")
    banner_url: Optional[str] = Field(None, description="Series banner image")
    
    # Status
    status: SeriesStatus = Field(..., description="Series status")
    is_featured: bool = Field(False, description="Featured series flag")
    
    # Organization
    episode_count: int = Field(0, description="Total number of episodes")
    season_count: int = Field(1, description="Number of seasons")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = Field(None, description="Publication date")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class SeriesStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"
```

### Episode Model
```python
class Episode(BaseModel):
    id: str = Field(..., description="Unique episode identifier")
    series_id: str = Field(..., description="Parent series ID")
    content_id: str = Field(..., description="Associated content ID")
    
    # Episode Information
    episode_number: int = Field(..., description="Episode number in series")
    season_number: int = Field(1, description="Season number")
    
    title: Dict[str, str] = Field(..., description="Episode title (ar/en)")
    description: Dict[str, str] = Field(..., description="Episode description")
    
    # Organization
    order_index: int = Field(..., description="Display order within series")
    is_featured_episode: bool = Field(False, description="Featured episode flag")
    
    # Scheduling
    scheduled_publish_at: Optional[datetime] = Field(None, description="Scheduled publication")
    published_at: Optional[datetime] = Field(None, description="Actual publication date")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default={}, description="Episode-specific metadata")
```

### Category Model
```python
class Category(BaseModel):
    id: str = Field(..., description="Unique category identifier")
    name: Dict[str, str] = Field(..., description="Category name (ar/en)")
    description: Dict[str, str] = Field(..., description="Category description")
    slug: Dict[str, str] = Field(..., description="URL-friendly category slug")
    
    # Hierarchy
    parent_id: Optional[str] = Field(None, description="Parent category ID")
    level: int = Field(0, description="Category level in hierarchy")
    path: str = Field(..., description="Full category path")
    
    # Display
    icon_url: Optional[str] = Field(None, description="Category icon")
    color: Optional[str] = Field(None, description="Category color theme")
    order_index: int = Field(0, description="Display order")
    
    # Status
    is_active: bool = Field(True, description="Category active status")
    is_featured: bool = Field(False, description="Featured category flag")
    
    # Statistics
    content_count: int = Field(0, description="Number of associated content items")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Tag Model
```python
class Tag(BaseModel):
    id: str = Field(..., description="Unique tag identifier")
    name: Dict[str, str] = Field(..., description="Tag name (ar/en)")
    slug: Dict[str, str] = Field(..., description="URL-friendly tag slug")
    description: Optional[Dict[str, str]] = Field(None, description="Tag description")
    
    # Classification
    type: TagType = Field(TagType.GENERAL, description="Tag type classification")
    color: Optional[str] = Field(None, description="Tag color for UI")
    
    # Statistics
    usage_count: int = Field(0, description="Number of times tag is used")
    
    # Status
    is_active: bool = Field(True, description="Tag active status")
    is_trending: bool = Field(False, description="Trending tag flag")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TagType(str, Enum):
    GENERAL = "general"
    TOPIC = "topic"
    SPEAKER = "speaker"
    EVENT = "event"
    LOCATION = "location"
    KEYWORD = "keyword"
```

### Content Relationship Model
```python
class ContentRelationship(BaseModel):
    id: str = Field(..., description="Unique relationship identifier")
    source_content_id: str = Field(..., description="Source content ID")
    target_content_id: str = Field(..., description="Target content ID")
    
    # Relationship
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    strength: float = Field(1.0, description="Relationship strength (0.0-1.0)")
    
    # Configuration
    is_bidirectional: bool = Field(True, description="Bidirectional relationship")
    is_manual: bool = Field(False, description="Manually created relationship")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RelationshipType(str, Enum):
    RELATED = "related"
    SEQUEL = "sequel"
    PREQUEL = "prequel"
    SIMILAR_TOPIC = "similar_topic"
    SAME_SPEAKER = "same_speaker"
    SAME_SERIES = "same_series"
    RECOMMENDED = "recommended"
```

---

## API Endpoints

### Series Management
```python
# Series CRUD
POST   /api/v1/series                    # Create series
GET    /api/v1/series                    # List series (with pagination/filtering)
GET    /api/v1/series/{series_id}        # Get series details
PUT    /api/v1/series/{series_id}        # Update series
DELETE /api/v1/series/{series_id}        # Delete series
PATCH  /api/v1/series/{series_id}/status # Update series status

# Series Episodes
GET    /api/v1/series/{series_id}/episodes              # Get series episodes
POST   /api/v1/series/{series_id}/episodes              # Add episode to series
PUT    /api/v1/series/{series_id}/episodes/order        # Reorder episodes
DELETE /api/v1/series/{series_id}/episodes/{episode_id} # Remove episode from series

# Series Features
POST   /api/v1/series/{series_id}/feature   # Feature series
DELETE /api/v1/series/{series_id}/feature   # Unfeature series
GET    /api/v1/series/featured              # Get featured series
```

### Category Management
```python
# Category CRUD
POST   /api/v1/categories                     # Create category
GET    /api/v1/categories                     # List categories (hierarchical)
GET    /api/v1/categories/tree                # Get category tree
GET    /api/v1/categories/{category_id}       # Get category details
PUT    /api/v1/categories/{category_id}       # Update category
DELETE /api/v1/categories/{category_id}       # Delete category

# Category Content
GET    /api/v1/categories/{category_id}/content # Get category content
POST   /api/v1/categories/{category_id}/content # Assign content to category

# Category Features
POST   /api/v1/categories/{category_id}/feature # Feature category
DELETE /api/v1/categories/{category_id}/feature # Unfeature category
```

### Tag Management
```python
# Tag CRUD
POST   /api/v1/tags              # Create tag
GET    /api/v1/tags              # List tags (with filtering)
GET    /api/v1/tags/trending     # Get trending tags
GET    /api/v1/tags/{tag_id}     # Get tag details
PUT    /api/v1/tags/{tag_id}     # Update tag
DELETE /api/v1/tags/{tag_id}     # Delete tag

# Tag Assignment
POST   /api/v1/content/{content_id}/tags     # Assign tags to content
DELETE /api/v1/content/{content_id}/tags     # Remove tags from content
GET    /api/v1/tags/{tag_id}/content         # Get tagged content
```

### Content Relationships
```python
# Relationship Management
POST   /api/v1/relationships                           # Create relationship
GET    /api/v1/relationships                           # List relationships
GET    /api/v1/content/{content_id}/relationships      # Get content relationships
PUT    /api/v1/relationships/{relationship_id}         # Update relationship
DELETE /api/v1/relationships/{relationship_id}         # Delete relationship

# Related Content
GET    /api/v1/content/{content_id}/related            # Get related content
POST   /api/v1/content/{content_id}/related            # Add related content
DELETE /api/v1/content/{content_id}/related/{target_id} # Remove relationship
```

### Publication Scheduling
```python
# Scheduling
POST   /api/v1/content/{content_id}/schedule    # Schedule content publication
GET    /api/v1/content/scheduled                # Get scheduled content
PUT    /api/v1/content/{content_id}/schedule    # Update schedule
DELETE /api/v1/content/{content_id}/schedule    # Cancel schedule

# Publishing
POST   /api/v1/content/{content_id}/publish     # Publish content immediately
POST   /api/v1/content/bulk-publish             # Bulk publish content
GET    /api/v1/content/publishing-queue         # Get publishing queue
```

---

## Core Workflows

### Series Creation Workflow
```python
async def create_series_workflow(series_data: SeriesCreateRequest) -> Series:
    """Complete series creation with validation and setup"""
    
    # 1. Validate series data
    await validate_series_data(series_data)
    
    # 2. Generate series slug
    slug = await generate_series_slug(series_data.title)
    
    # 3. Create series record
    series = await create_series(series_data, slug)
    
    # 4. Setup default categories/tags if provided
    if series_data.categories:
        await assign_series_categories(series.id, series_data.categories)
    
    if series_data.tags:
        await assign_series_tags(series.id, series_data.tags)
    
    # 5. Update search index
    await update_search_index(series)
    
    # 6. Send creation notification
    await notify_series_created(series)
    
    return series
```

### Episode Addition Workflow
```python
async def add_episode_to_series_workflow(
    series_id: str, 
    content_id: str, 
    episode_data: EpisodeCreateRequest
) -> Episode:
    """Add episode to series with proper ordering"""
    
    # 1. Validate series exists and is active
    series = await get_series(series_id)
    if not series or series.status == SeriesStatus.ARCHIVED:
        raise SeriesNotFoundError()
    
    # 2. Validate content exists and is not already in series
    content = await get_content(content_id)
    await validate_episode_not_exists(series_id, content_id)
    
    # 3. Determine episode number and order
    next_episode_number = await get_next_episode_number(series_id, episode_data.season_number)
    order_index = await calculate_episode_order_index(series_id, episode_data)
    
    # 4. Create episode record
    episode = await create_episode({
        **episode_data.dict(),
        "series_id": series_id,
        "content_id": content_id,
        "episode_number": next_episode_number,
        "order_index": order_index
    })
    
    # 5. Update series episode count
    await increment_series_episode_count(series_id)
    
    # 6. Update content with series information
    await update_content_series_info(content_id, series_id, episode.id)
    
    # 7. Update search indexes
    await update_series_search_index(series_id)
    await update_content_search_index(content_id)
    
    # 8. Send notifications
    await notify_episode_added(series, episode)
    
    return episode
```

### Content Relationship Analysis
```python
async def analyze_content_relationships_workflow(content_id: str) -> List[ContentRelationship]:
    """Analyze and create automatic content relationships"""
    
    # 1. Get content metadata
    content = await get_content_metadata(content_id)
    
    # 2. Find similar content by various criteria
    relationships = []
    
    # Same series episodes
    if content.series_id:
        series_episodes = await find_related_series_episodes(content.series_id, content_id)
        relationships.extend([
            ContentRelationship(
                source_content_id=content_id,
                target_content_id=episode.content_id,
                relationship_type=RelationshipType.SAME_SERIES,
                strength=0.9,
                is_manual=False
            ) for episode in series_episodes[:5]
        ])
    
    # Similar topics/tags
    similar_by_tags = await find_similar_content_by_tags(content_id, limit=10)
    relationships.extend([
        ContentRelationship(
            source_content_id=content_id,
            target_content_id=similar.id,
            relationship_type=RelationshipType.SIMILAR_TOPIC,
            strength=similar.similarity_score,
            is_manual=False
        ) for similar in similar_by_tags
    ])
    
    # Same speaker/creator
    if content.speaker_tags:
        same_speaker = await find_content_by_speaker(content.speaker_tags, content_id, limit=5)
        relationships.extend([
            ContentRelationship(
                source_content_id=content_id,
                target_content_id=speaker_content.id,
                relationship_type=RelationshipType.SAME_SPEAKER,
                strength=0.8,
                is_manual=False
            ) for speaker_content in same_speaker
        ])
    
    # 3. Create relationship records
    created_relationships = []
    for rel in relationships:
        if not await relationship_exists(rel.source_content_id, rel.target_content_id):
            created_rel = await create_content_relationship(rel)
            created_relationships.append(created_rel)
    
    # 4. Update content search index with relationships
    await update_content_relationships_index(content_id)
    
    return created_relationships
```

### Publication Scheduling Workflow
```python
async def schedule_content_publication_workflow(
    content_id: str, 
    schedule_request: PublicationScheduleRequest
) -> PublicationSchedule:
    """Schedule content for future publication"""
    
    # 1. Validate content exists and is in draft status
    content = await get_content(content_id)
    if content.status != ContentStatus.DRAFT:
        raise InvalidContentStatusError("Only draft content can be scheduled")
    
    # 2. Validate schedule time is in future
    if schedule_request.publish_at <= datetime.utcnow():
        raise InvalidScheduleTimeError("Schedule time must be in the future")
    
    # 3. Create publication schedule
    schedule = await create_publication_schedule({
        "content_id": content_id,
        "scheduled_publish_at": schedule_request.publish_at,
        "timezone": schedule_request.timezone or "UTC",
        "auto_feature": schedule_request.auto_feature or False,
        "notification_settings": schedule_request.notification_settings
    })
    
    # 4. Update content status to scheduled
    await update_content_status(content_id, ContentStatus.SCHEDULED)
    
    # 5. Create background job for publication
    await create_publication_job(schedule)
    
    # 6. Send scheduling confirmation
    await notify_content_scheduled(content, schedule)
    
    return schedule
```

---

## Performance Requirements

### Response Time Targets
```yaml
Series Operations:
  - Series list (paginated): <150ms (95th percentile)
  - Series details: <100ms (95th percentile)
  - Series creation: <300ms (95th percentile)
  - Episode addition: <200ms (95th percentile)

Category Operations:
  - Category tree: <100ms (95th percentile)
  - Category content: <200ms (95th percentile)
  - Category creation: <150ms (95th percentile)

Tag Operations:
  - Tag search/autocomplete: <50ms (95th percentile)
  - Tag assignment: <100ms (95th percentile)
  - Trending tags: <100ms (95th percentile)

Relationship Operations:
  - Related content: <200ms (95th percentile)
  - Relationship analysis: <500ms (background)
  - Relationship creation: <150ms (95th percentile)
```

### Throughput Targets
```yaml
Series Management:
  - Series operations: 100 requests/second
  - Episode operations: 200 requests/second
  - Concurrent series creation: 10/second

Category Management:
  - Category operations: 500 requests/second
  - Category tree requests: 1000 requests/second
  - Content categorization: 100 requests/second

Tag Management:
  - Tag operations: 1000 requests/second
  - Tag search/autocomplete: 2000 requests/second
  - Tag assignment: 500 requests/second

Relationship Management:
  - Related content queries: 1000 requests/second
  - Relationship operations: 100 requests/second
  - Background analysis: 50 content items/minute
```

### Data Scale Expectations
```yaml
Content Volume:
  - Series: Up to 10,000 series
  - Episodes: Up to 100,000 episodes
  - Categories: Up to 1,000 categories (hierarchical)
  - Tags: Up to 50,000 tags
  - Relationships: Up to 1 million relationships

Operational Scale:
  - Daily content organization: 1,000 items
  - Daily series operations: 100 series
  - Daily tag operations: 5,000 assignments
  - Background relationship analysis: 10,000 items/day
```

---

## Integration Points

### Internal Service Integration
```yaml
Content Management Service:
  - Content metadata retrieval
  - Content status updates
  - Content validation
  - Series assignment updates

Search & Discovery Service:
  - Search index updates
  - Category/tag faceting
  - Related content search
  - Trending content analysis

Analytics & Reporting Service:
  - Content performance data
  - Category analytics
  - Tag usage statistics
  - Series engagement metrics

Notification Service:
  - Series creation alerts
  - Publication schedule notifications
  - Featured content announcements
  - Relationship discovery alerts
```

### External Service Integration
```yaml
Database Integration:
  - PostgreSQL (primary data store)
  - Redis (caching, session data)
  - OpenSearch (search indexing)

Messaging Integration:
  - NATS (event publishing)
  - Background job queue
  - Real-time notifications

CDN Integration:
  - Series thumbnail delivery
  - Category icon caching
  - Static asset optimization
```

### Event Publishing
```yaml
Series Events:
  - series.created
  - series.updated
  - series.published
  - series.featured
  - episode.added
  - episode.reordered

Category Events:
  - category.created
  - category.updated
  - category.content_assigned
  - category.featured

Tag Events:
  - tag.created
  - tag.assigned
  - tag.trending
  - tag.usage_updated

Relationship Events:
  - relationship.created
  - relationship.updated
  - relationship.analyzed
  - related_content.updated

Publication Events:
  - content.scheduled
  - content.published
  - schedule.updated
  - publication.completed
```

---

## Security & Compliance

### Access Control
```yaml
Content Managers:
  - Full series and episode management
  - Category management (all levels)
  - Tag management and assignment
  - Content relationship management
  - Publication scheduling

Content Editors:
  - Series episode assignment
  - Tag assignment to own content
  - Basic category assignment
  - Read-only relationship viewing

System Services:
  - Automated relationship analysis
  - Background publication processing
  - Search index updates
  - Analytics data collection

Public API:
  - Read-only category tree access
  - Public tag listing
  - Published series information
  - Featured content access
```

### Data Validation
```yaml
Input Validation:
  - Series/episode title length limits
  - Category hierarchy depth limits
  - Tag name format validation
  - Relationship strength range validation
  - Schedule time validation

Content Validation:
  - Series-episode relationship integrity
  - Category hierarchy consistency
  - Tag assignment limits per content
  - Circular relationship prevention
  - Publication schedule conflicts

Data Integrity:
  - Orphaned episode cleanup
  - Category reference validation
  - Tag usage count accuracy
  - Relationship bidirectionality
  - Series statistics consistency
```

### Audit Logging
```yaml
Tracked Operations:
  - All series create/update/delete operations
  - Episode additions and reordering
  - Category management operations
  - Tag assignments and modifications
  - Content relationship changes
  - Publication scheduling and execution
  - Featured content management

Audit Data:
  - User ID and role
  - Operation timestamp
  - Before/after data states
  - IP address and user agent
  - API endpoint accessed
  - Success/failure status
  - Error details if applicable
```

This comprehensive Content Organization Service specification provides the foundation for managing content taxonomy, series relationships, and publication workflows within the thmnayah platform.