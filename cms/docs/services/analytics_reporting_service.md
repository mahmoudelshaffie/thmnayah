# Analytics & Reporting Service

## Service Overview

**Responsibility**: Usage analytics, content performance, and reporting  
**Domain**: Business intelligence and insights  
**Data**: Usage metrics, content analytics, reports  
**Users**: Content managers, system admins

## Core Features

### Content Performance Tracking
- Content view and engagement metrics
- Content popularity and trending analysis
- Content consumption patterns and duration
- Content sharing and referral tracking
- Content search and discovery analytics

### User Engagement Analytics
- User behavior and interaction patterns
- User journey and content flow analysis
- User retention and churn analysis
- User segmentation and profiling
- User preference and recommendation analytics

### Import Job Monitoring
- Import process success/failure rates
- Import performance and bottleneck analysis
- Data quality and transformation metrics
- Import source performance comparison
- Import scheduling and optimization analytics

### System Health Reporting
- Service performance and availability metrics
- Resource utilization and capacity planning
- Error rates and system reliability
- API performance and response time analytics
- Infrastructure cost and optimization tracking

### Custom Dashboards
- Real-time executive dashboards
- Content manager operational dashboards
- Performance monitoring dashboards
- Business intelligence reporting
- Custom KPI and metric visualizations

---

## Technical Specifications

### Tech Stack
```yaml
Runtime: Python 3.11+
Framework: FastAPI 0.104+
Database: 
  - ClickHouse 23+ (time-series analytics)
  - PostgreSQL 15+ (metadata and aggregations)
  - Redis 7+ (real-time data and caching)
Analytics Engine: Apache Spark 3.5+ (batch processing)
Streaming: Apache Kafka 3.5+ / AWS Kinesis
Visualization: Grafana 10+, Apache Superset 3+
Message Queue: NATS 2.10+
Monitoring: Prometheus + Grafana
Testing: pytest, asyncio-compatible
```

### Dependencies
```yaml
Internal Services:
  - Content Management Service (content metadata)
  - User Management Service (user data)
  - Media Processing Service (processing metrics)
  - Import Service (import job data)
  - Search & Discovery Service (search analytics)

External Services:
  - ClickHouse (analytics database)
  - PostgreSQL (metadata storage)
  - Redis (real-time caching)
  - Kafka/Kinesis (event streaming)
  - Apache Spark (data processing)
  - Grafana (visualization)
```

---

## Data Models

### Analytics Event Model
```python
class AnalyticsEvent(BaseModel):
    id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type (view, click, search, etc.)")
    event_category: str = Field(..., description="Event category (content, user, system)")
    
    # Event Data
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Context
    content_id: Optional[str] = Field(None, description="Related content ID")
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource identifier")
    
    # Technical Context
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    referrer: Optional[str] = Field(None, description="Referrer URL")
    
    # Geographic Context
    country: Optional[str] = Field(None, description="User country")
    region: Optional[str] = Field(None, description="User region")
    city: Optional[str] = Field(None, description="User city")
    
    # Custom Properties
    properties: Dict[str, Any] = Field(default={}, description="Additional event properties")
    
    # Processing
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    batch_id: Optional[str] = Field(None, description="Processing batch ID")

class EventType(str, Enum):
    # Content Events
    CONTENT_VIEW = "content_view"
    CONTENT_PLAY = "content_play"
    CONTENT_PAUSE = "content_pause"
    CONTENT_COMPLETE = "content_complete"
    CONTENT_SHARE = "content_share"
    CONTENT_BOOKMARK = "content_bookmark"
    
    # Search Events
    SEARCH_QUERY = "search_query"
    SEARCH_RESULT_CLICK = "search_result_click"
    SEARCH_FILTER = "search_filter"
    
    # User Events
    USER_REGISTER = "user_register"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    
    # System Events
    API_REQUEST = "api_request"
    ERROR_OCCURRED = "error_occurred"
    IMPORT_STARTED = "import_started"
    IMPORT_COMPLETED = "import_completed"
```

### Content Analytics Model
```python
class ContentAnalytics(BaseModel):
    content_id: str = Field(..., description="Content identifier")
    date: date = Field(..., description="Analytics date")
    
    # View Metrics
    total_views: int = Field(0, description="Total content views")
    unique_views: int = Field(0, description="Unique user views")
    average_view_duration: float = Field(0.0, description="Average view duration (seconds)")
    completion_rate: float = Field(0.0, description="View completion rate (0.0-1.0)")
    
    # Engagement Metrics
    likes: int = Field(0, description="Total likes")
    shares: int = Field(0, description="Total shares")
    bookmarks: int = Field(0, description="Total bookmarks")
    comments: int = Field(0, description="Total comments")
    
    # Discovery Metrics
    search_impressions: int = Field(0, description="Search result impressions")
    search_clicks: int = Field(0, description="Search result clicks")
    recommendation_impressions: int = Field(0, description="Recommendation impressions")
    recommendation_clicks: int = Field(0, description="Recommendation clicks")
    
    # Traffic Sources
    direct_traffic: int = Field(0, description="Direct access")
    search_traffic: int = Field(0, description="Search-driven traffic")
    recommendation_traffic: int = Field(0, description="Recommendation-driven traffic")
    external_traffic: int = Field(0, description="External referral traffic")
    
    # Geographic Distribution
    top_countries: Dict[str, int] = Field(default={}, description="View count by country")
    top_regions: Dict[str, int] = Field(default={}, description="View count by region")
    
    # Device Analytics
    desktop_views: int = Field(0, description="Desktop views")
    mobile_views: int = Field(0, description="Mobile views")
    tablet_views: int = Field(0, description="Tablet views")
    
    # Time-based Analytics
    hourly_distribution: Dict[int, int] = Field(default={}, description="Views by hour (0-23)")
    daily_trend: float = Field(0.0, description="Daily trend percentage")
    
    # Performance Scores
    popularity_score: float = Field(0.0, description="Content popularity score")
    engagement_score: float = Field(0.0, description="Content engagement score")
    quality_score: float = Field(0.0, description="Content quality score")
    
    # Timestamps
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
```

### User Analytics Model
```python
class UserAnalytics(BaseModel):
    user_id: str = Field(..., description="User identifier")
    date: date = Field(..., description="Analytics date")
    
    # Activity Metrics
    sessions: int = Field(0, description="Number of sessions")
    total_session_duration: float = Field(0.0, description="Total session duration (seconds)")
    average_session_duration: float = Field(0.0, description="Average session duration")
    
    # Content Consumption
    content_views: int = Field(0, description="Total content views")
    unique_content_views: int = Field(0, description="Unique content items viewed")
    total_watch_time: float = Field(0.0, description="Total content watch time")
    content_completions: int = Field(0, description="Content completion count")
    
    # Engagement Actions
    searches_performed: int = Field(0, description="Number of searches")
    shares_made: int = Field(0, description="Number of shares")
    bookmarks_created: int = Field(0, description="Number of bookmarks")
    comments_made: int = Field(0, description="Number of comments")
    
    # User Journey
    pages_visited: int = Field(0, description="Number of pages visited")
    bounce_rate: float = Field(0.0, description="User bounce rate")
    return_visits: int = Field(0, description="Number of return visits")
    
    # Preferences
    preferred_categories: Dict[str, int] = Field(default={}, description="Category preferences")
    preferred_languages: Dict[str, int] = Field(default={}, description="Language preferences")
    preferred_content_types: Dict[str, int] = Field(default={}, description="Content type preferences")
    
    # Device Usage
    device_types: Dict[str, int] = Field(default={}, description="Device type usage")
    browser_types: Dict[str, int] = Field(default={}, description="Browser usage")
    
    # Behavioral Scores
    engagement_score: float = Field(0.0, description="User engagement score")
    loyalty_score: float = Field(0.0, description="User loyalty score")
    activity_score: float = Field(0.0, description="User activity score")
    
    # Timestamps
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
```

### System Analytics Model
```python
class SystemAnalytics(BaseModel):
    service_name: str = Field(..., description="Service name")
    date: date = Field(..., description="Analytics date")
    hour: int = Field(..., description="Hour (0-23)")
    
    # Performance Metrics
    request_count: int = Field(0, description="Total requests")
    success_count: int = Field(0, description="Successful requests")
    error_count: int = Field(0, description="Error requests")
    average_response_time: float = Field(0.0, description="Average response time (ms)")
    
    # Resource Utilization
    cpu_usage_avg: float = Field(0.0, description="Average CPU usage (%)")
    memory_usage_avg: float = Field(0.0, description="Average memory usage (%)")
    disk_usage_avg: float = Field(0.0, description="Average disk usage (%)")
    
    # API Analytics
    endpoint_stats: Dict[str, Dict[str, Any]] = Field(default={}, description="Per-endpoint statistics")
    status_code_distribution: Dict[str, int] = Field(default={}, description="HTTP status codes")
    
    # Database Performance
    db_query_count: int = Field(0, description="Database query count")
    db_avg_query_time: float = Field(0.0, description="Average query time (ms)")
    db_slow_queries: int = Field(0, description="Slow query count")
    
    # Cache Performance
    cache_hits: int = Field(0, description="Cache hit count")
    cache_misses: int = Field(0, description="Cache miss count")
    cache_hit_rate: float = Field(0.0, description="Cache hit rate")
    
    # External Dependencies
    external_api_calls: int = Field(0, description="External API calls")
    external_api_errors: int = Field(0, description="External API errors")
    external_avg_response_time: float = Field(0.0, description="External API response time")
    
    # Timestamps
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Report Model
```python
class Report(BaseModel):
    id: str = Field(..., description="Unique report identifier")
    name: str = Field(..., description="Report name")
    description: Optional[str] = Field(None, description="Report description")
    
    # Report Configuration
    report_type: ReportType = Field(..., description="Report type")
    report_format: ReportFormat = Field(..., description="Output format")
    
    # Data Configuration
    data_source: str = Field(..., description="Data source")
    date_range: DateRange = Field(..., description="Report date range")
    filters: Dict[str, Any] = Field(default={}, description="Report filters")
    
    # Visualization
    chart_type: Optional[str] = Field(None, description="Chart type")
    visualization_config: Dict[str, Any] = Field(default={}, description="Visualization settings")
    
    # Scheduling
    is_scheduled: bool = Field(False, description="Scheduled report flag")
    schedule_config: Optional[Dict[str, Any]] = Field(None, description="Schedule configuration")
    
    # Access Control
    created_by: str = Field(..., description="Report creator")
    shared_with: List[str] = Field(default=[], description="Shared user IDs")
    is_public: bool = Field(False, description="Public report flag")
    
    # Status
    status: ReportStatus = Field(ReportStatus.DRAFT, description="Report status")
    last_generated: Optional[datetime] = Field(None, description="Last generation time")
    
    # Output
    output_url: Optional[str] = Field(None, description="Generated report URL")
    file_size: Optional[int] = Field(None, description="Report file size")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ReportType(str, Enum):
    CONTENT_PERFORMANCE = "content_performance"
    USER_ENGAGEMENT = "user_engagement"
    SYSTEM_HEALTH = "system_health"
    IMPORT_SUMMARY = "import_summary"
    SEARCH_ANALYTICS = "search_analytics"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"

class ReportStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class DateRange(BaseModel):
    start_date: date = Field(..., description="Range start date")
    end_date: date = Field(..., description="Range end date")
    period_type: str = Field("daily", description="Period granularity")
```

---

## API Endpoints

### Event Tracking
```python
# Event Collection
POST   /api/v1/analytics/events                # Track single event
POST   /api/v1/analytics/events/batch          # Track multiple events
GET    /api/v1/analytics/events                # Query events (admin)
GET    /api/v1/analytics/events/{event_id}     # Get event details

# Real-time Tracking
POST   /api/v1/analytics/track/content-view    # Track content view
POST   /api/v1/analytics/track/search          # Track search query
POST   /api/v1/analytics/track/user-action     # Track user action
GET    /api/v1/analytics/real-time             # Get real-time metrics
```

### Content Analytics
```python
# Content Performance
GET    /api/v1/analytics/content/{content_id}           # Get content analytics
GET    /api/v1/analytics/content                        # Get content analytics (bulk)
GET    /api/v1/analytics/content/trending               # Get trending content
GET    /api/v1/analytics/content/top-performing         # Get top performing content

# Content Insights
GET    /api/v1/analytics/content/{content_id}/insights  # Get content insights
GET    /api/v1/analytics/content/{content_id}/audience  # Get content audience
GET    /api/v1/analytics/content/{content_id}/journey   # Get user journey for content
GET    /api/v1/analytics/content/comparison             # Compare content performance
```

### User Analytics
```python
# User Engagement
GET    /api/v1/analytics/users/{user_id}        # Get user analytics
GET    /api/v1/analytics/users                  # Get user analytics (aggregated)
GET    /api/v1/analytics/users/segments         # Get user segments
GET    /api/v1/analytics/users/cohorts          # Get cohort analysis

# User Insights
GET    /api/v1/analytics/users/{user_id}/journey     # Get user journey
GET    /api/v1/analytics/users/{user_id}/preferences # Get user preferences
GET    /api/v1/analytics/users/behavior-patterns     # Get behavior patterns
GET    /api/v1/analytics/users/retention             # Get retention analysis
```

### System Analytics
```python
# System Performance
GET    /api/v1/analytics/system/health          # Get system health metrics
GET    /api/v1/analytics/system/performance     # Get performance metrics
GET    /api/v1/analytics/system/errors          # Get error analytics
GET    /api/v1/analytics/system/usage           # Get system usage stats

# Service Analytics
GET    /api/v1/analytics/services/{service_name}    # Get service analytics
GET    /api/v1/analytics/services                   # Get all services analytics
GET    /api/v1/analytics/api/endpoints              # Get API endpoint analytics
GET    /api/v1/analytics/database/performance       # Get database performance
```

### Import Analytics
```python
# Import Monitoring
GET    /api/v1/analytics/imports/jobs           # Get import job analytics
GET    /api/v1/analytics/imports/sources        # Get import source performance
GET    /api/v1/analytics/imports/quality        # Get data quality metrics
GET    /api/v1/analytics/imports/trends         # Get import trend analysis

# Import Insights
GET    /api/v1/analytics/imports/{job_id}       # Get specific job analytics
GET    /api/v1/analytics/imports/failures       # Get import failure analysis
GET    /api/v1/analytics/imports/optimization   # Get optimization recommendations
```

### Reporting
```python
# Report Management
POST   /api/v1/analytics/reports               # Create report
GET    /api/v1/analytics/reports               # List reports
GET    /api/v1/analytics/reports/{report_id}   # Get report details
PUT    /api/v1/analytics/reports/{report_id}   # Update report
DELETE /api/v1/analytics/reports/{report_id}   # Delete report

# Report Generation
POST   /api/v1/analytics/reports/{report_id}/generate    # Generate report
GET    /api/v1/analytics/reports/{report_id}/download    # Download report
GET    /api/v1/analytics/reports/{report_id}/status      # Get generation status
POST   /api/v1/analytics/reports/{report_id}/schedule    # Schedule report

# Report Sharing
POST   /api/v1/analytics/reports/{report_id}/share       # Share report
GET    /api/v1/analytics/reports/shared                  # Get shared reports
PUT    /api/v1/analytics/reports/{report_id}/permissions # Update permissions
```

### Dashboard APIs
```python
# Dashboard Management
POST   /api/v1/analytics/dashboards            # Create dashboard
GET    /api/v1/analytics/dashboards            # List dashboards
GET    /api/v1/analytics/dashboards/{id}       # Get dashboard
PUT    /api/v1/analytics/dashboards/{id}       # Update dashboard
DELETE /api/v1/analytics/dashboards/{id}       # Delete dashboard

# Dashboard Data
GET    /api/v1/analytics/dashboards/{id}/data  # Get dashboard data
GET    /api/v1/analytics/widgets/{widget_id}   # Get widget data
POST   /api/v1/analytics/widgets               # Create widget
PUT    /api/v1/analytics/widgets/{widget_id}   # Update widget
```

---

## Core Workflows

### Event Processing Workflow
```python
async def process_analytics_events_workflow(events: List[AnalyticsEvent]) -> ProcessingResult:
    """Process analytics events with real-time and batch processing"""
    
    # 1. Validate and sanitize events
    validated_events = []
    for event in events:
        try:
            # Validate event structure
            validated_event = await validate_analytics_event(event)
            
            # Enrich with additional context
            enriched_event = await enrich_event_context(validated_event)
            
            validated_events.append(enriched_event)
        except Exception as e:
            await log_event_validation_error(event, e)
    
    # 2. Real-time processing for immediate metrics
    real_time_results = []
    for event in validated_events:
        if event.event_type in REAL_TIME_EVENTS:
            # Update real-time counters in Redis
            await update_real_time_metrics(event)
            
            # Trigger real-time alerts if needed
            await check_real_time_alerts(event)
            
            real_time_results.append(event.id)
    
    # 3. Queue for batch processing
    batch_processing_results = []
    if validated_events:
        # Send to Kafka/Kinesis for batch processing
        batch_id = await queue_for_batch_processing(validated_events)
        batch_processing_results.append(batch_id)
        
        # Store events in ClickHouse for long-term analytics
        await store_events_in_clickhouse(validated_events)
    
    # 4. Update aggregation tables
    await trigger_aggregation_updates(validated_events)
    
    return ProcessingResult(
        processed_count=len(validated_events),
        real_time_updates=len(real_time_results),
        batch_jobs=len(batch_processing_results),
        errors=len(events) - len(validated_events)
    )
```

### Content Analytics Calculation
```python
async def calculate_content_analytics_workflow(content_id: str, date_range: DateRange) -> ContentAnalytics:
    """Calculate comprehensive content analytics for given period"""
    
    # 1. Retrieve raw events from ClickHouse
    raw_events = await get_content_events(content_id, date_range)
    
    # 2. Calculate view metrics
    view_events = [e for e in raw_events if e.event_type == EventType.CONTENT_VIEW]
    unique_users = len(set(e.user_id for e in view_events if e.user_id))
    
    # Calculate viewing duration and completion
    play_events = [e for e in raw_events if e.event_type == EventType.CONTENT_PLAY]
    pause_events = [e for e in raw_events if e.event_type == EventType.CONTENT_PAUSE]
    complete_events = [e for e in raw_events if e.event_type == EventType.CONTENT_COMPLETE]
    
    total_watch_time = await calculate_total_watch_time(play_events, pause_events)
    completion_rate = len(complete_events) / max(len(view_events), 1)
    
    # 3. Calculate engagement metrics
    engagement_events = [e for e in raw_events if e.event_type in [
        EventType.CONTENT_SHARE, 
        EventType.CONTENT_BOOKMARK,
        "content_like",
        "content_comment"
    ]]
    
    engagement_by_type = {}
    for event in engagement_events:
        engagement_by_type[event.event_type] = engagement_by_type.get(event.event_type, 0) + 1
    
    # 4. Calculate discovery metrics
    search_events = [e for e in raw_events if e.event_type == EventType.SEARCH_RESULT_CLICK and 
                     e.properties.get('content_id') == content_id]
    recommendation_events = [e for e in raw_events if 
                           e.event_type == 'recommendation_click' and 
                           e.properties.get('content_id') == content_id]
    
    # 5. Analyze traffic sources
    traffic_sources = await analyze_traffic_sources(view_events)
    
    # 6. Geographic and device analysis
    geographic_data = await analyze_geographic_distribution(view_events)
    device_data = await analyze_device_distribution(view_events)
    
    # 7. Calculate performance scores
    popularity_score = await calculate_popularity_score(content_id, view_events, engagement_events)
    engagement_score = await calculate_engagement_score(view_events, engagement_events)
    quality_score = await calculate_quality_score(content_id, completion_rate, engagement_score)
    
    # 8. Create analytics record
    analytics = ContentAnalytics(
        content_id=content_id,
        date=date_range.end_date,
        total_views=len(view_events),
        unique_views=unique_users,
        average_view_duration=total_watch_time / max(len(view_events), 1),
        completion_rate=completion_rate,
        likes=engagement_by_type.get("content_like", 0),
        shares=engagement_by_type.get(EventType.CONTENT_SHARE, 0),
        bookmarks=engagement_by_type.get(EventType.CONTENT_BOOKMARK, 0),
        search_clicks=len(search_events),
        recommendation_clicks=len(recommendation_events),
        **traffic_sources,
        **geographic_data,
        **device_data,
        popularity_score=popularity_score,
        engagement_score=engagement_score,
        quality_score=quality_score
    )
    
    # 9. Store analytics data
    await store_content_analytics(analytics)
    
    # 10. Update content performance rankings
    await update_content_rankings(content_id, analytics)
    
    return analytics
```

### Report Generation Workflow
```python
async def generate_report_workflow(report_id: str) -> ReportGenerationResult:
    """Generate comprehensive analytics report"""
    
    # 1. Get report configuration
    report = await get_report(report_id)
    if not report:
        raise ReportNotFoundError()
    
    # 2. Update report status
    await update_report_status(report_id, ReportStatus.GENERATING)
    
    try:
        # 3. Collect data based on report type
        if report.report_type == ReportType.CONTENT_PERFORMANCE:
            data = await collect_content_performance_data(report)
        elif report.report_type == ReportType.USER_ENGAGEMENT:
            data = await collect_user_engagement_data(report)
        elif report.report_type == ReportType.SYSTEM_HEALTH:
            data = await collect_system_health_data(report)
        elif report.report_type == ReportType.IMPORT_SUMMARY:
            data = await collect_import_summary_data(report)
        elif report.report_type == ReportType.SEARCH_ANALYTICS:
            data = await collect_search_analytics_data(report)
        else:
            data = await collect_custom_report_data(report)
        
        # 4. Apply filters and transformations
        filtered_data = await apply_report_filters(data, report.filters)
        transformed_data = await transform_report_data(filtered_data, report)
        
        # 5. Generate visualizations if needed
        visualizations = []
        if report.chart_type:
            visualizations = await generate_report_visualizations(
                transformed_data, 
                report.chart_type, 
                report.visualization_config
            )
        
        # 6. Generate report in specified format
        if report.report_format == ReportFormat.PDF:
            output_file = await generate_pdf_report(transformed_data, visualizations, report)
        elif report.report_format == ReportFormat.EXCEL:
            output_file = await generate_excel_report(transformed_data, visualizations, report)
        elif report.report_format == ReportFormat.CSV:
            output_file = await generate_csv_report(transformed_data, report)
        elif report.report_format == ReportFormat.JSON:
            output_file = await generate_json_report(transformed_data, report)
        else:
            output_file = await generate_html_report(transformed_data, visualizations, report)
        
        # 7. Upload to S3 and get URL
        output_url = await upload_report_to_s3(output_file, report_id)
        
        # 8. Update report with output information
        await update_report_completion(report_id, {
            "status": ReportStatus.COMPLETED,
            "output_url": output_url,
            "file_size": output_file.size,
            "last_generated": datetime.utcnow()
        })
        
        # 9. Send notifications if configured
        if report.shared_with:
            await notify_report_completion(report, output_url)
        
        # 10. Clean up temporary files
        await cleanup_report_temp_files(output_file)
        
        return ReportGenerationResult(
            report_id=report_id,
            status="completed",
            output_url=output_url,
            file_size=output_file.size,
            generation_time=datetime.utcnow()
        )
    
    except Exception as e:
        # Handle generation failure
        await update_report_status(report_id, ReportStatus.FAILED)
        await log_report_generation_error(report_id, e)
        
        return ReportGenerationResult(
            report_id=report_id,
            status="failed",
            error=str(e),
            generation_time=datetime.utcnow()
        )
```

### Real-time Dashboard Updates
```python
async def update_real_time_dashboard_workflow(dashboard_id: str) -> DashboardUpdateResult:
    """Update real-time dashboard with latest metrics"""
    
    # 1. Get dashboard configuration
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise DashboardNotFoundError()
    
    # 2. Get all widgets in dashboard
    widgets = await get_dashboard_widgets(dashboard_id)
    
    updated_widgets = []
    for widget in widgets:
        try:
            # 3. Update widget data based on type
            if widget.widget_type == "real_time_counter":
                data = await get_real_time_counter_data(widget.config)
            elif widget.widget_type == "trending_content":
                data = await get_trending_content_data(widget.config)
            elif widget.widget_type == "user_activity":
                data = await get_user_activity_data(widget.config)
            elif widget.widget_type == "system_health":
                data = await get_system_health_data(widget.config)
            elif widget.widget_type == "custom_metric":
                data = await get_custom_metric_data(widget.config)
            else:
                continue
            
            # 4. Update widget cache
            await update_widget_cache(widget.id, data)
            
            # 5. Push to real-time subscribers
            await push_widget_update(widget.id, data)
            
            updated_widgets.append(widget.id)
            
        except Exception as e:
            await log_widget_update_error(widget.id, e)
    
    # 6. Update dashboard last refresh time
    await update_dashboard_refresh_time(dashboard_id)
    
    return DashboardUpdateResult(
        dashboard_id=dashboard_id,
        updated_widgets=updated_widgets,
        update_time=datetime.utcnow()
    )
```

---

## Performance Requirements

### Response Time Targets
```yaml
Real-time Analytics:
  - Event tracking: <50ms (95th percentile)
  - Real-time metrics: <100ms (95th percentile)
  - Dashboard updates: <200ms (95th percentile)
  - Live counters: <50ms (95th percentile)

Analytics Queries:
  - Content analytics: <500ms (95th percentile)
  - User analytics: <300ms (95th percentile)
  - System metrics: <200ms (95th percentile)
  - Aggregated data: <1000ms (95th percentile)

Report Generation:
  - Simple reports: <30 seconds (95th percentile)
  - Complex reports: <2 minutes (95th percentile)
  - Dashboard creation: <5 seconds (95th percentile)
  - Data export: <1 minute (95th percentile)

Batch Processing:
  - Event processing: <5 minutes (hourly batch)
  - Analytics calculation: <15 minutes (daily batch)
  - Aggregation updates: <30 minutes (daily batch)
```

### Throughput Targets
```yaml
Event Processing:
  - Event ingestion: 10,000 events/second
  - Real-time processing: 5,000 events/second
  - Batch processing: 100,000 events/minute
  - Event validation: 50,000 events/second

Analytics Queries:
  - Concurrent analytics queries: 1,000 queries/second
  - Real-time dashboard updates: 500 updates/second
  - Report API requests: 100 requests/second
  - Data export requests: 50 requests/second

Data Storage:
  - Event storage: 1 billion events/month
  - Analytics data retention: 24 months
  - Report storage: 10,000 reports/month
  - Dashboard configurations: 1,000 dashboards
```

### Data Scale Expectations
```yaml
Event Volume:
  - Daily events: Up to 10 million events
  - Peak hourly events: Up to 1 million events
  - Event types: 50+ different event types
  - Event retention: 24 months of data

Analytics Data:
  - Content analytics records: 1 million/month
  - User analytics records: 100,000/month
  - System analytics records: 1 million/month
  - Aggregated metrics: 10 million data points

Reporting:
  - Active reports: 1,000 reports
  - Scheduled reports: 500 reports
  - Dashboard configurations: 200 dashboards
  - Report generation: 100 reports/day
```

---

## Integration Points

### Internal Service Integration
```yaml
Content Management Service:
  - Content metadata for analytics
  - Content performance tracking
  - Content lifecycle events
  - Content categorization data

User Management Service:
  - User activity tracking
  - User profile analytics
  - Authentication events
  - User segmentation data

Import Service:
  - Import job monitoring
  - Import performance metrics
  - Data quality tracking
  - Import success/failure rates

Search & Discovery Service:
  - Search query analytics
  - Search result performance
  - User discovery patterns
  - Recommendation effectiveness

Media Processing Service:
  - Processing job metrics
  - Media conversion analytics
  - Processing performance data
  - Resource utilization metrics
```

### External Service Integration
```yaml
Data Infrastructure:
  - ClickHouse (time-series analytics)
  - PostgreSQL (metadata and aggregations)
  - Redis (real-time metrics, caching)
  - Apache Kafka/Kinesis (event streaming)
  - Apache Spark (batch processing)

Visualization Platforms:
  - Grafana (system monitoring dashboards)
  - Apache Superset (business intelligence)
  - Custom dashboard APIs
  - Report generation engines

Cloud Services:
  - AWS S3 (report storage)
  - AWS CloudWatch (system metrics)
  - AWS QuickSight (business analytics)
  - AWS Kinesis Analytics (stream processing)

Notification Services:
  - Email notifications for reports
  - Slack/Teams integration
  - Webhook notifications
  - Real-time alerts
```

### Event Publishing
```yaml
Analytics Events:
  - analytics.event_processed
  - analytics.aggregation_completed
  - analytics.report_generated
  - analytics.alert_triggered

Performance Events:
  - performance.threshold_exceeded
  - performance.anomaly_detected
  - performance.optimization_suggested
  - performance.sla_violated

System Events:
  - system.health_check_completed
  - system.resource_usage_updated
  - system.error_rate_changed
  - system.capacity_warning

Business Events:
  - business.kpi_updated
  - business.goal_achieved
  - business.trend_detected
  - business.insight_generated
```

---

## Security & Compliance

### Data Privacy
```yaml
Personal Data Protection:
  - User activity anonymization options
  - GDPR compliance for analytics data
  - Data retention policy enforcement
  - User consent for analytics tracking
  - Right to be forgotten implementation

Data Access Control:
  - Role-based analytics access
  - Row-level security for sensitive data
  - API access controls
  - Report sharing permissions
  - Dashboard access restrictions
```

### Security Measures
```yaml
Data Security:
  - Encryption at rest for analytics data
  - Secure data transmission
  - API authentication and authorization
  - Audit logging for all analytics operations
  - Secure report generation and storage

Analytics Security:
  - SQL injection prevention
  - Query performance limits
  - Resource usage monitoring
  - Anomaly detection for unusual queries
  - Rate limiting for analytics APIs
```

### Compliance Requirements
```yaml
Regulatory Compliance:
  - GDPR data processing compliance
  - Data retention and deletion policies
  - User consent management
  - Cross-border data transfer regulations
  - Industry-specific compliance requirements

Audit and Governance:
  - Complete audit trail for all operations
  - Data lineage and provenance tracking
  - Change management for analytics configurations
  - Compliance reporting capabilities
  - Regular security assessments
```

This comprehensive Analytics & Reporting Service specification provides the foundation for data-driven decision making and business intelligence within the thmnayah platform.