# Notification Service

## Service Overview

**Responsibility**: Event-driven notifications and communications  
**Domain**: Cross-service communication and user notifications  
**Data**: Notification templates, delivery logs, user preferences  
**Users**: All system users

## Core Features

### Real-time Notifications
- In-app notifications and alerts
- WebSocket-based real-time messaging
- Push notifications to mobile devices
- Browser push notifications
- Real-time activity feeds and updates

### Email Notifications
- Transactional email delivery
- Marketing and promotional emails
- Email template management and rendering
- Multi-language email support (Arabic/English)
- Email scheduling and automation

### Event-driven Messaging
- NATS integration for service communication
- Event subscription and processing
- Message queuing and delivery guarantees
- Cross-service notification coordination
- Event-based workflow automation

### Notification Preferences
- User notification preference management
- Channel-specific preference settings
- Frequency and timing controls
- Notification category management
- Do-not-disturb and quiet hours

### Delivery Tracking
- Notification delivery status tracking
- Read/unread status management
- Delivery failure handling and retry logic
- Analytics and reporting on notification performance
- A/B testing for notification effectiveness

---

## Technical Specifications

### Tech Stack
```yaml
Runtime: Python 3.11+
Framework: FastAPI 0.104+
Database: PostgreSQL 15+ (primary), Redis 7+ (caching)
Message Queue: NATS 2.10+
Email Service: AWS SES / SendGrid
Push Services: FCM (Firebase), APNs (Apple Push)
WebSocket: Socket.IO / native WebSocket
Template Engine: Jinja2
Monitoring: Prometheus + Grafana
Testing: pytest, asyncio-compatible
```

### Dependencies
```yaml
Internal Services:
  - User Management Service (user profiles, preferences)
  - Content Management Service (content-related notifications)
  - Analytics Service (notification analytics)
  - All other services (event sources)

External Services:
  - AWS SES / SendGrid (email delivery)
  - Firebase Cloud Messaging (push notifications)
  - Apple Push Notification Service (iOS push)
  - PostgreSQL (notification data)
  - Redis (real-time data, caching)
  - NATS (event messaging)
```

---

## Data Models

### Notification Model
```python
class Notification(BaseModel):
    id: str = Field(..., description="Unique notification identifier")
    
    # Recipient Information
    user_id: str = Field(..., description="Target user ID")
    recipient_email: Optional[str] = Field(None, description="Email address")
    recipient_phone: Optional[str] = Field(None, description="Phone number")
    
    # Notification Content
    title: Dict[str, str] = Field(..., description="Notification title (ar/en)")
    message: Dict[str, str] = Field(..., description="Notification message (ar/en)")
    summary: Optional[Dict[str, str]] = Field(None, description="Short summary")
    
    # Classification
    notification_type: NotificationType = Field(..., description="Type of notification")
    category: str = Field(..., description="Notification category")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Priority level")
    
    # Content References
    related_entity_type: Optional[str] = Field(None, description="Related entity type")
    related_entity_id: Optional[str] = Field(None, description="Related entity ID")
    
    # Delivery Configuration
    channels: List[NotificationChannel] = Field(..., description="Delivery channels")
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled delivery time")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    
    # Status and Tracking
    status: NotificationStatus = Field(NotificationStatus.PENDING, description="Notification status")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    
    # Delivery Tracking
    delivery_attempts: int = Field(0, description="Number of delivery attempts")
    last_delivery_attempt: Optional[datetime] = Field(None, description="Last delivery attempt")
    delivery_failures: List[Dict[str, Any]] = Field(default=[], description="Delivery failure log")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    template_data: Dict[str, Any] = Field(default={}, description="Template rendering data")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationType(str, Enum):
    SYSTEM = "system"
    CONTENT = "content"
    USER_ACTION = "user_action"
    SECURITY = "security"
    MARKETING = "marketing"
    IMPORT = "import"
    ANALYTICS = "analytics"
    REMINDER = "reminder"

class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    WEBHOOK = "webhook"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
```

### Notification Template Model
```python
class NotificationTemplate(BaseModel):
    id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    
    # Template Content
    subject_template: Dict[str, str] = Field(..., description="Subject template (ar/en)")
    body_template: Dict[str, str] = Field(..., description="Body template (ar/en)")
    html_template: Optional[Dict[str, str]] = Field(None, description="HTML template (ar/en)")
    
    # Template Configuration
    template_type: NotificationType = Field(..., description="Template type")
    category: str = Field(..., description="Template category")
    supported_channels: List[NotificationChannel] = Field(..., description="Supported channels")
    
    # Template Variables
    required_variables: List[str] = Field(default=[], description="Required template variables")
    optional_variables: List[str] = Field(default=[], description="Optional template variables")
    variable_schema: Dict[str, Any] = Field(default={}, description="Variable validation schema")
    
    # Styling and Formatting
    styling_config: Dict[str, Any] = Field(default={}, description="Template styling configuration")
    formatting_rules: Dict[str, Any] = Field(default={}, description="Content formatting rules")
    
    # Status and Versioning
    is_active: bool = Field(True, description="Template active status")
    version: str = Field("1.0", description="Template version")
    parent_template_id: Optional[str] = Field(None, description="Parent template for versioning")
    
    # Usage Tracking
    usage_count: int = Field(0, description="Number of times used")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Template creator")
```

### User Notification Preferences Model
```python
class UserNotificationPreferences(BaseModel):
    user_id: str = Field(..., description="User identifier")
    
    # Global Settings
    notifications_enabled: bool = Field(True, description="Global notification toggle")
    preferred_language: str = Field("en", description="Preferred language (ar/en)")
    preferred_timezone: str = Field("UTC", description="User timezone")
    
    # Channel Preferences
    email_enabled: bool = Field(True, description="Email notifications enabled")
    push_enabled: bool = Field(True, description="Push notifications enabled")
    in_app_enabled: bool = Field(True, description="In-app notifications enabled")
    sms_enabled: bool = Field(False, description="SMS notifications enabled")
    
    # Category Preferences
    category_preferences: Dict[str, NotificationCategoryPreference] = Field(
        default={}, description="Per-category preferences"
    )
    
    # Frequency Controls
    digest_frequency: DigestFrequency = Field(DigestFrequency.DAILY, description="Digest frequency")
    max_notifications_per_hour: int = Field(10, description="Hourly notification limit")
    max_notifications_per_day: int = Field(50, description="Daily notification limit")
    
    # Quiet Hours
    quiet_hours_enabled: bool = Field(False, description="Quiet hours enabled")
    quiet_hours_start: Optional[time] = Field(None, description="Quiet hours start time")
    quiet_hours_end: Optional[time] = Field(None, description="Quiet hours end time")
    quiet_hours_timezone: str = Field("UTC", description="Quiet hours timezone")
    
    # Device Tokens
    device_tokens: List[DeviceToken] = Field(default=[], description="Device tokens for push")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationCategoryPreference(BaseModel):
    enabled: bool = Field(True, description="Category enabled")
    channels: List[NotificationChannel] = Field(default=[], description="Preferred channels")
    frequency: str = Field("immediate", description="Notification frequency")
    priority_filter: NotificationPriority = Field(NotificationPriority.LOW, description="Minimum priority")

class DigestFrequency(str, Enum):
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    DISABLED = "disabled"

class DeviceToken(BaseModel):
    token: str = Field(..., description="Device token")
    platform: str = Field(..., description="Platform (ios, android, web)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = Field(None, description="Last used timestamp")
```

### Notification Event Model
```python
class NotificationEvent(BaseModel):
    id: str = Field(..., description="Unique event identifier")
    
    # Event Information
    event_type: str = Field(..., description="Event type that triggered notification")
    event_source: str = Field(..., description="Source service that generated event")
    event_data: Dict[str, Any] = Field(..., description="Event payload")
    
    # Processing Information
    triggered_notifications: List[str] = Field(default=[], description="Triggered notification IDs")
    processing_status: str = Field("pending", description="Event processing status")
    processing_errors: List[str] = Field(default=[], description="Processing errors")
    
    # Routing Information
    target_users: List[str] = Field(default=[], description="Target user IDs")
    notification_rules: List[str] = Field(default=[], description="Applied notification rules")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(None, description="Processing completion time")
```

### Delivery Log Model
```python
class DeliveryLog(BaseModel):
    id: str = Field(..., description="Unique delivery log identifier")
    notification_id: str = Field(..., description="Related notification ID")
    
    # Delivery Information
    channel: NotificationChannel = Field(..., description="Delivery channel")
    recipient: str = Field(..., description="Recipient identifier")
    
    # Status and Timing
    status: DeliveryStatus = Field(..., description="Delivery status")
    attempted_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    
    # Delivery Details
    provider: Optional[str] = Field(None, description="Delivery provider")
    provider_message_id: Optional[str] = Field(None, description="Provider message ID")
    provider_response: Dict[str, Any] = Field(default={}, description="Provider response")
    
    # Error Information
    error_code: Optional[str] = Field(None, description="Error code")
    error_message: Optional[str] = Field(None, description="Error message")
    retry_count: int = Field(0, description="Number of retries")
    
    # Metadata
    delivery_metadata: Dict[str, Any] = Field(default={}, description="Additional delivery metadata")

class DeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"
    OPENED = "opened"
    CLICKED = "clicked"
```

---

## API Endpoints

### Notification Management
```python
# Notification CRUD
POST   /api/v1/notifications                    # Create notification
GET    /api/v1/notifications                    # List notifications (with filtering)
GET    /api/v1/notifications/{notification_id} # Get notification details
PUT    /api/v1/notifications/{notification_id} # Update notification
DELETE /api/v1/notifications/{notification_id} # Delete notification
POST   /api/v1/notifications/batch             # Create multiple notifications

# Notification Actions
POST   /api/v1/notifications/{notification_id}/send    # Send notification
POST   /api/v1/notifications/{notification_id}/cancel  # Cancel notification
POST   /api/v1/notifications/{notification_id}/reschedule # Reschedule notification
PATCH  /api/v1/notifications/{notification_id}/read    # Mark as read
```

### Template Management
```python
# Template CRUD
POST   /api/v1/templates                # Create notification template
GET    /api/v1/templates                # List templates
GET    /api/v1/templates/{template_id}  # Get template details
PUT    /api/v1/templates/{template_id}  # Update template
DELETE /api/v1/templates/{template_id} # Delete template

# Template Operations
POST   /api/v1/templates/{template_id}/preview    # Preview template
POST   /api/v1/templates/{template_id}/test       # Send test notification
POST   /api/v1/templates/{template_id}/duplicate  # Duplicate template
GET    /api/v1/templates/{template_id}/usage      # Get template usage stats
```

### User Notifications
```python
# User Notification Management
GET    /api/v1/users/{user_id}/notifications           # Get user notifications
GET    /api/v1/users/me/notifications                  # Get current user notifications
PATCH  /api/v1/users/me/notifications/mark-all-read   # Mark all as read
DELETE /api/v1/users/me/notifications                  # Delete all notifications

# Notification Preferences
GET    /api/v1/users/{user_id}/notification-preferences # Get preferences
PUT    /api/v1/users/{user_id}/notification-preferences # Update preferences
GET    /api/v1/users/me/notification-preferences         # Get current user preferences
PUT    /api/v1/users/me/notification-preferences         # Update current user preferences

# Device Management
POST   /api/v1/users/me/devices                    # Register device token
GET    /api/v1/users/me/devices                    # Get registered devices
DELETE /api/v1/users/me/devices/{device_id}       # Remove device token
PUT    /api/v1/users/me/devices/{device_id}       # Update device token
```

### Event Processing
```python
# Event Handling
POST   /api/v1/notifications/events                # Process notification event
GET    /api/v1/notifications/events                # List notification events
GET    /api/v1/notifications/events/{event_id}     # Get event details
POST   /api/v1/notifications/events/replay         # Replay failed events

# Event Subscriptions
POST   /api/v1/notifications/subscriptions         # Create event subscription
GET    /api/v1/notifications/subscriptions         # List subscriptions
PUT    /api/v1/notifications/subscriptions/{id}    # Update subscription
DELETE /api/v1/notifications/subscriptions/{id}    # Delete subscription
```

### Delivery Tracking
```python
# Delivery Status
GET    /api/v1/notifications/{notification_id}/delivery     # Get delivery status
GET    /api/v1/notifications/delivery-logs                  # Get delivery logs
GET    /api/v1/delivery/stats                               # Get delivery statistics
POST   /api/v1/delivery/retry                               # Retry failed deliveries

# Webhooks for External Providers
POST   /api/v1/webhooks/email/ses                           # AWS SES webhook
POST   /api/v1/webhooks/email/sendgrid                      # SendGrid webhook
POST   /api/v1/webhooks/push/fcm                            # FCM webhook
```

### Real-time Features
```python
# WebSocket Endpoints
WebSocket /ws/notifications/{user_id}           # User-specific notification stream
WebSocket /ws/notifications/global              # Global notification stream
WebSocket /ws/system/health                     # System health notifications

# Server-Sent Events
GET    /api/v1/notifications/stream/{user_id}   # SSE for user notifications
GET    /api/v1/notifications/stream/admin       # SSE for admin notifications
```

### Analytics and Reporting
```python
# Notification Analytics
GET    /api/v1/analytics/notifications                      # General notification analytics
GET    /api/v1/analytics/notifications/delivery-rates      # Delivery rate analytics
GET    /api/v1/analytics/notifications/engagement          # Engagement analytics
GET    /api/v1/analytics/templates/{template_id}/performance # Template performance

# Reports
POST   /api/v1/reports/notifications                        # Generate notification report
GET    /api/v1/reports/notifications                        # List notification reports
GET    /api/v1/reports/notifications/{report_id}            # Get report details
```

---

## Core Workflows

### Notification Creation and Delivery Workflow
```python
async def create_and_send_notification_workflow(
    notification_request: NotificationCreateRequest
) -> NotificationResponse:
    """Create and deliver notification with full lifecycle management"""
    
    # 1. Validate notification request
    await validate_notification_request(notification_request)
    
    # 2. Get user notification preferences
    user_preferences = await get_user_notification_preferences(notification_request.user_id)
    
    # 3. Check if notification should be sent based on preferences
    should_send = await check_notification_eligibility(notification_request, user_preferences)
    if not should_send:
        await log_notification_filtered(notification_request, "user_preferences")
        return NotificationResponse(status="filtered", reason="user_preferences")
    
    # 4. Apply rate limiting
    rate_limit_check = await check_notification_rate_limits(
        notification_request.user_id, 
        notification_request.category
    )
    if not rate_limit_check.allowed:
        await schedule_notification_for_later(notification_request)
        return NotificationResponse(status="rate_limited", scheduled_for=rate_limit_check.next_available)
    
    # 5. Create notification record
    notification = await create_notification({
        **notification_request.dict(),
        "status": NotificationStatus.PENDING
    })
    
    # 6. Process template if template_id provided
    if notification_request.template_id:
        rendered_content = await render_notification_template(
            notification_request.template_id,
            notification_request.template_data,
            user_preferences.preferred_language
        )
        notification.title = rendered_content.title
        notification.message = rendered_content.message
    
    # 7. Determine delivery channels based on preferences and request
    delivery_channels = await determine_delivery_channels(notification_request, user_preferences)
    
    # 8. Send via each channel
    delivery_results = []
    for channel in delivery_channels:
        try:
            if channel == NotificationChannel.EMAIL:
                result = await send_email_notification(notification, user_preferences)
            elif channel == NotificationChannel.PUSH:
                result = await send_push_notification(notification, user_preferences)
            elif channel == NotificationChannel.IN_APP:
                result = await send_in_app_notification(notification)
            elif channel == NotificationChannel.SMS:
                result = await send_sms_notification(notification, user_preferences)
            
            delivery_results.append(result)
            await create_delivery_log(notification.id, channel, result)
            
        except Exception as e:
            await handle_delivery_failure(notification.id, channel, e)
            delivery_results.append(DeliveryResult(channel=channel, status="failed", error=str(e)))
    
    # 9. Update notification status
    overall_status = determine_overall_delivery_status(delivery_results)
    await update_notification_status(notification.id, overall_status)
    
    # 10. Send delivery analytics event
    await track_notification_delivery(notification.id, delivery_results)
    
    # 11. Handle post-delivery actions
    if overall_status == NotificationStatus.SENT:
        await trigger_post_delivery_actions(notification)
    
    return NotificationResponse(
        notification_id=notification.id,
        status=overall_status,
        delivery_results=delivery_results,
        created_at=notification.created_at
    )
```

### Event-Driven Notification Processing
```python
async def process_notification_event_workflow(event: NotificationEvent) -> EventProcessingResult:
    """Process incoming events and trigger appropriate notifications"""
    
    # 1. Validate and parse event
    try:
        validated_event = await validate_notification_event(event)
    except ValidationError as e:
        await log_event_validation_error(event, e)
        return EventProcessingResult(status="invalid", error=str(e))
    
    # 2. Find applicable notification rules
    notification_rules = await find_notification_rules_for_event(validated_event.event_type)
    
    if not notification_rules:
        await log_no_rules_found(validated_event)
        return EventProcessingResult(status="no_rules", processed_count=0)
    
    # 3. Process each notification rule
    triggered_notifications = []
    processing_errors = []
    
    for rule in notification_rules:
        try:
            # Check rule conditions
            if not await evaluate_rule_conditions(rule, validated_event):
                continue
            
            # Determine target users
            target_users = await determine_target_users(rule, validated_event)
            
            # Create notifications for each target user
            for user_id in target_users:
                notification_request = await build_notification_from_rule(
                    rule, validated_event, user_id
                )
                
                # Create and send notification
                result = await create_and_send_notification_workflow(notification_request)
                
                if result.status in ["sent", "scheduled"]:
                    triggered_notifications.append(result.notification_id)
                else:
                    processing_errors.append(f"Failed to send notification to user {user_id}: {result.reason}")
        
        except Exception as e:
            processing_errors.append(f"Error processing rule {rule.id}: {str(e)}")
            await log_rule_processing_error(rule.id, validated_event.id, e)
    
    # 4. Update event processing status
    await update_event_processing_status(validated_event.id, {
        "processing_status": "completed",
        "triggered_notifications": triggered_notifications,
        "processing_errors": processing_errors,
        "processed_at": datetime.utcnow()
    })
    
    # 5. Send processing analytics
    await track_event_processing(validated_event.id, len(triggered_notifications), len(processing_errors))
    
    return EventProcessingResult(
        event_id=validated_event.id,
        status="completed",
        processed_count=len(triggered_notifications),
        error_count=len(processing_errors),
        errors=processing_errors
    )
```

### Template Rendering Workflow
```python
async def render_notification_template_workflow(
    template_id: str,
    template_data: Dict[str, Any],
    language: str = "en"
) -> RenderedTemplate:
    """Render notification template with provided data"""
    
    # 1. Get template from database
    template = await get_notification_template(template_id)
    if not template:
        raise TemplateNotFoundError(f"Template {template_id} not found")
    
    if not template.is_active:
        raise TemplateInactiveError(f"Template {template_id} is inactive")
    
    # 2. Validate template data against schema
    if template.variable_schema:
        await validate_template_data(template_data, template.variable_schema)
    
    # 3. Check required variables
    missing_vars = []
    for required_var in template.required_variables:
        if required_var not in template_data:
            missing_vars.append(required_var)
    
    if missing_vars:
        raise TemplateValidationError(f"Missing required variables: {', '.join(missing_vars)}")
    
    # 4. Prepare rendering context
    rendering_context = {
        **template_data,
        "current_time": datetime.utcnow(),
        "current_date": date.today(),
        "language": language,
        "platform": "thmnayah"
    }
    
    # 5. Apply formatting rules
    if template.formatting_rules:
        rendering_context = await apply_formatting_rules(
            rendering_context, 
            template.formatting_rules
        )
    
    # 6. Render templates
    try:
        # Render subject
        subject_template = template.subject_template.get(language, template.subject_template.get("en", ""))
        rendered_subject = await render_jinja_template(subject_template, rendering_context)
        
        # Render body
        body_template = template.body_template.get(language, template.body_template.get("en", ""))
        rendered_body = await render_jinja_template(body_template, rendering_context)
        
        # Render HTML if available
        rendered_html = None
        if template.html_template:
            html_template = template.html_template.get(language, template.html_template.get("en", ""))
            if html_template:
                rendered_html = await render_jinja_template(html_template, rendering_context)
    
    except Exception as e:
        await log_template_rendering_error(template_id, e)
        raise TemplateRenderingError(f"Failed to render template: {str(e)}")
    
    # 7. Apply styling if configured
    if template.styling_config:
        rendered_html = await apply_template_styling(rendered_html, template.styling_config)
    
    # 8. Update template usage statistics
    await update_template_usage_stats(template_id)
    
    # 9. Cache rendered template if cacheable
    if template_data.get("cache_key"):
        await cache_rendered_template(template_data["cache_key"], {
            "subject": rendered_subject,
            "body": rendered_body,
            "html": rendered_html
        })
    
    return RenderedTemplate(
        template_id=template_id,
        language=language,
        subject=rendered_subject,
        body=rendered_body,
        html=rendered_html,
        rendered_at=datetime.utcnow()
    )
```

### User Preference Management Workflow
```python
async def update_user_notification_preferences_workflow(
    user_id: str,
    preference_updates: UserNotificationPreferenceUpdate
) -> UserNotificationPreferences:
    """Update user notification preferences with validation and side effects"""
    
    # 1. Get current preferences
    current_preferences = await get_user_notification_preferences(user_id)
    if not current_preferences:
        # Create default preferences for new user
        current_preferences = await create_default_user_preferences(user_id)
    
    # 2. Validate preference updates
    await validate_preference_updates(preference_updates)
    
    # 3. Apply updates to current preferences
    updated_preferences = await merge_preference_updates(current_preferences, preference_updates)
    
    # 4. Handle device token updates
    if preference_updates.device_tokens:
        # Validate device tokens
        for device_token in preference_updates.device_tokens:
            await validate_device_token(device_token)
        
        # Update device token registrations
        await update_device_token_registrations(user_id, preference_updates.device_tokens)
    
    # 5. Handle channel-specific preference changes
    if preference_updates.email_enabled is False:
        # Cancel any scheduled email notifications
        await cancel_scheduled_email_notifications(user_id)
    
    if preference_updates.push_enabled is False:
        # Unregister push notification tokens
        await unregister_push_tokens(user_id)
    
    # 6. Update category preferences
    if preference_updates.category_preferences:
        for category, prefs in preference_updates.category_preferences.items():
            await update_category_notification_rules(user_id, category, prefs)
    
    # 7. Handle quiet hours changes
    if preference_updates.quiet_hours_enabled is not None:
        if preference_updates.quiet_hours_enabled:
            await schedule_quiet_hours_processor(user_id, updated_preferences)
        else:
            await cancel_quiet_hours_processor(user_id)
    
    # 8. Save updated preferences
    saved_preferences = await save_user_notification_preferences(updated_preferences)
    
    # 9. Clear preference cache
    await clear_user_preference_cache(user_id)
    
    # 10. Send preference update confirmation
    if preference_updates.send_confirmation:
        await send_preference_update_confirmation(user_id, saved_preferences)
    
    # 11. Log preference changes for audit
    await log_preference_changes(user_id, current_preferences, saved_preferences)
    
    # 12. Update user analytics
    await track_preference_update(user_id, preference_updates)
    
    return saved_preferences
```

---

## Performance Requirements

### Response Time Targets
```yaml
Real-time Notifications:
  - In-app notification delivery: <100ms (95th percentile)
  - WebSocket message delivery: <50ms (95th percentile)
  - Push notification triggering: <200ms (95th percentile)
  - Real-time status updates: <100ms (95th percentile)

Notification Operations:
  - Notification creation: <200ms (95th percentile)
  - Template rendering: <150ms (95th percentile)
  - Preference updates: <300ms (95th percentile)
  - Event processing: <500ms (95th percentile)

Email Operations:
  - Email composition: <300ms (95th percentile)
  - Email queuing: <100ms (95th percentile)
  - Email delivery (external): <5 seconds (95th percentile)
  - Delivery status update: <200ms (95th percentile)

Batch Operations:
  - Bulk notification creation: <2 seconds (1000 notifications)
  - Template batch rendering: <5 seconds (1000 renders)
  - Preference bulk updates: <10 seconds (1000 users)
  - Event batch processing: <30 seconds (10000 events)
```

### Throughput Targets
```yaml
Notification Processing:
  - Notification creation: 1,000 notifications/second
  - Real-time delivery: 5,000 notifications/second
  - Email processing: 10,000 emails/hour
  - Push notifications: 50,000 notifications/minute

Event Processing:
  - Event ingestion: 10,000 events/second
  - Event processing: 5,000 events/second
  - Rule evaluation: 50,000 evaluations/second
  - Template rendering: 2,000 renders/second

User Operations:
  - Preference updates: 500 updates/second
  - Device registration: 1,000 registrations/second
  - Notification queries: 5,000 queries/second
  - WebSocket connections: 10,000 concurrent connections
```

### Data Scale Expectations
```yaml
Notification Data:
  - Daily notifications: Up to 1 million notifications
  - Active templates: Up to 500 templates
  - User preferences: Up to 100,000 preference sets
  - Delivery logs: Up to 5 million log entries/month

Event Processing:
  - Daily events: Up to 10 million events
  - Event rules: Up to 1,000 notification rules
  - Event subscriptions: Up to 10,000 subscriptions
  - Processing queues: Up to 100,000 queued items

Real-time Connections:
  - Concurrent WebSocket connections: Up to 10,000
  - Active device tokens: Up to 50,000 tokens
  - Real-time message throughput: 1,000 messages/second
  - Connection lifecycle: 24-hour connection duration
```

---

## Integration Points

### Internal Service Integration
```yaml
User Management Service:
  - User profile data for personalization
  - User authentication and authorization
  - User preference synchronization
  - User activity tracking

Content Management Service:
  - Content-related notification triggers
  - Content metadata for notifications
  - Content lifecycle events
  - Content sharing and engagement events

Analytics Service:
  - Notification performance tracking
  - User engagement analytics
  - Delivery success metrics
  - A/B testing for notifications

Import Service:
  - Import job completion notifications
  - Import status updates
  - Import error alerts
  - Data quality notifications

All Services:
  - Event-driven notification triggers
  - System health alerts
  - Error and exception notifications
  - Operational status updates
```

### External Service Integration
```yaml
Email Services:
  - AWS SES (transactional email)
  - SendGrid (marketing email)
  - Email delivery tracking
  - Bounce and complaint handling

Push Notification Services:
  - Firebase Cloud Messaging (Android/Web)
  - Apple Push Notification Service (iOS)
  - Push delivery tracking
  - Token management

Messaging Infrastructure:
  - NATS (event messaging)
  - Redis (real-time data)
  - WebSocket connections
  - Server-sent events

Database Services:
  - PostgreSQL (persistent data)
  - Redis (caching, sessions)
  - ClickHouse (analytics data)
  - Time-series data storage
```

### Event Publishing
```yaml
Notification Events:
  - notification.created
  - notification.sent
  - notification.delivered
  - notification.read
  - notification.failed

Template Events:
  - template.created
  - template.updated
  - template.used
  - template.performance_updated

User Preference Events:
  - preferences.updated
  - device.registered
  - device.unregistered
  - subscription.changed

Delivery Events:
  - delivery.attempted
  - delivery.succeeded
  - delivery.failed
  - delivery.bounced

System Events:
  - rate_limit.exceeded
  - queue.full
  - service.unhealthy
  - performance.degraded
```

---

## Security & Compliance

### Data Privacy
```yaml
Personal Data Protection:
  - User consent for notification types
  - GDPR compliance for communication data
  - Data retention policies
  - Right to unsubscribe implementation
  - Personal data anonymization options

Communication Privacy:
  - End-to-end encryption for sensitive notifications
  - Secure template storage
  - Protected user preferences
  - Audit trail for all communications
  - Data minimization practices
```

### Security Measures
```yaml
Authentication and Authorization:
  - API authentication for all endpoints
  - Role-based access for notification management
  - User permission validation
  - Service-to-service authentication
  - Admin access controls

Data Security:
  - Encryption at rest for notification data
  - Secure transmission of all communications
  - Template injection prevention
  - Input validation and sanitization
  - Rate limiting and abuse prevention

Delivery Security:
  - Secure email content handling
  - Push notification certificate management
  - Device token protection
  - Webhook signature verification
  - External service authentication
```

### Compliance Requirements
```yaml
Communication Compliance:
  - CAN-SPAM Act compliance
  - GDPR communication consent
  - Opt-out mechanism implementation
  - Communication frequency limits
  - Content appropriateness validation

Audit and Governance:
  - Complete notification audit trail
  - Delivery tracking and reporting
  - Performance monitoring and alerting
  - Compliance reporting capabilities
  - Regular security assessments

Privacy Controls:
  - User preference management
  - Communication opt-out options
  - Data export capabilities
  - Account deletion handling
  - Cross-border data transfer compliance
```

This comprehensive Notification Service specification provides the foundation for reliable, scalable, and compliant communication management within the thmnayah platform.