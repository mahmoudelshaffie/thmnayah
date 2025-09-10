"""
User Management Controller for Thmnayah CMS

This module handles user management operations including profile management,
user preferences, social media integration, and content personalization.

User Stories Implemented:
- As an admin, I can manage user accounts and permissions
- As a user, I can manage my profile and preferences
- As a user, I can set my preferred content languages
- As a user, I can manage my social media integrations
- As an admin, I can track user engagement and analytics
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status, Path
from pydantic import BaseModel, EmailStr

router = APIRouter()

class UserProfile(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    full_name: str
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    preferred_languages: List[str] = ["ar", "en"]
    timezone: str = "UTC"
    created_at: datetime
    last_active: datetime
    is_active: bool = True

class UserPreferences(BaseModel):
    content_types: List[str] = []
    categories: List[uuid.UUID] = []
    notification_settings: Dict[str, bool] = {}
    privacy_settings: Dict[str, Any] = {}
    content_filters: Dict[str, Any] = {}

@router.get("/", response_model=Dict[str, Any], summary="Get all users with filtering")
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    created_after: Optional[datetime] = Query(None, description="Filter users created after date"),
):
    """
    Get paginated list of users with optional filtering.
    
    User Story: As an admin, I need to view and search through user accounts
    to manage the platform effectively.
    
    Business Context:
    - Supports admin dashboard user management
    - Enables user search and filtering capabilities
    - Provides pagination for large user bases
    """
    # Generate realistic user data based on filters
    users = await _generate_users_list(
        page=page,
        limit=limit,
        search=search,
        is_active=is_active,
        role=role,
        created_after=created_after
    )
    
    # Apply search filtering
    if search:
        search_lower = search.lower()
        users = [
            user for user in users
            if search_lower in user.get("username", "").lower() or
               search_lower in user.get("email", "").lower() or
               search_lower in user.get("full_name", "").lower()
        ]
    
    # Apply active status filtering
    if is_active is not None:
        users = [user for user in users if user.get("is_active") == is_active]
    
    # Apply role filtering
    if role:
        users = [user for user in users if user.get("role") == role]
    
    # Apply date filtering
    if created_after:
        users = [
            user for user in users
            if datetime.fromisoformat(user.get("created_at", "").replace("Z", "+00:00")) >= created_after
        ]
    
    # Apply pagination
    total_users = len(users)
    offset = (page - 1) * limit
    paginated_users = users[offset:offset + limit]
    total_pages = (total_users + limit - 1) // limit
    
    # Calculate additional statistics
    active_count = len([u for u in users if u.get("is_active", True)])
    role_counts = {}
    for user in users:
        role = user.get("role", "user")
        role_counts[role] = role_counts.get(role, 0) + 1
    
    users_response = {
        "users": paginated_users,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_users,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "statistics": {
            "total_users": total_users,
            "active_users": active_count,
            "inactive_users": total_users - active_count,
            "role_distribution": role_counts,
            "new_users_today": len([
                u for u in users 
                if (datetime.utcnow() - datetime.fromisoformat(u.get("created_at", "").replace("Z", "+00:00"))).days == 0
            ]),
            "new_users_this_week": len([
                u for u in users 
                if (datetime.utcnow() - datetime.fromisoformat(u.get("created_at", "").replace("Z", "+00:00"))).days <= 7
            ])
        },
        "filters_applied": {
            "search": search,
            "is_active": is_active,
            "role": role,
            "created_after": created_after.isoformat() if created_after else None
        },
        "available_roles": list(role_counts.keys()),
        "query_time": 0.125  # Simulated query time
    }
    
    return users_response

@router.post("/", response_model=UserProfile, status_code=status.HTTP_201_CREATED, summary="Create new user")
async def create_user(
    user_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Create a new user account.
    
    User Story: As an admin, I can create user accounts with appropriate
    permissions and settings.
    
    Business Context:
    - Supports admin user creation workflow
    - Enables bulk user imports if needed
    - Triggers welcome email and profile setup
    """
    # Add background tasks for user creation
    background_tasks.add_task(_send_welcome_email, user_data.get("email"))
    background_tasks.add_task(_initialize_user_preferences, user_data.get("id"))
    
    # Validate required fields
    if not user_data.get("username"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required"
        )
    
    if not user_data.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    if not user_data.get("full_name"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name is required"
        )
    
    # Validate username uniqueness (simulate check)
    existing_usernames = ["admin", "root", "system", "ahmad_scholar", "fatima_student"]
    if user_data.get("username").lower() in [u.lower() for u in existing_usernames]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # Validate email uniqueness (simulate check)
    existing_emails = ["admin@example.com", "ahmad@example.com", "fatima@example.com"]
    if user_data.get("email").lower() in [e.lower() for e in existing_emails]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Validate username format
    username = user_data.get("username")
    if not username.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username can only contain letters, numbers, hyphens, and underscores"
        )
    
    if len(username) < 3 or len(username) > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be between 3 and 30 characters"
        )
    
    # Generate new user
    user_id = str(uuid.uuid4())
    current_time = datetime.utcnow()
    
    # Build comprehensive user profile
    new_user = {
        "id": user_id,
        "username": username,
        "email": user_data.get("email"),
        "full_name": user_data.get("full_name"),
        "profile_image_url": user_data.get("profile_image_url"),
        "bio": user_data.get("bio"),
        "preferred_languages": user_data.get("preferred_languages", ["ar", "en"]),
        "timezone": user_data.get("timezone", "Asia/Riyadh"),
        "role": user_data.get("role", "user"),
        "is_active": user_data.get("is_active", True),
        "email_verified": user_data.get("email_verified", False),
        "phone_number": user_data.get("phone_number"),
        "phone_verified": False,
        "two_factor_enabled": False,
        "created_at": current_time.isoformat(),
        "updated_at": current_time.isoformat(),
        "last_active": current_time.isoformat(),
        "last_login": None,
        "login_count": 0,
        "profile_completion": _calculate_profile_completion(user_data),
        "account_status": "pending_verification" if not user_data.get("email_verified") else "active",
        "created_by": user_data.get("created_by", "system"),  # Track who created the user
        "metadata": user_data.get("metadata", {}),
        "preferences": {
            "content_types": user_data.get("preferred_content_types", []),
            "categories": user_data.get("preferred_categories", []),
            "notification_settings": {
                "new_content": True,
                "series_updates": True,
                "social_interactions": True,
                "marketing": False,
                "email_notifications": True,
                "push_notifications": True
            },
            "privacy_settings": {
                "profile_visibility": "public",
                "activity_tracking": True,
                "personalized_ads": False,
                "data_sharing": False
            }
        },
        "statistics": {
            "content_views": 0,
            "content_created": 0,
            "social_shares": 0,
            "engagement_score": 0
        }
    }
    
    # Schedule background tasks for user initialization
    background_tasks.add_task(
        lambda: None  # _send_welcome_email implementation
    )
    background_tasks.add_task(
        lambda: None  # _initialize_user_preferences implementation
    )
    
    # Send verification email if not already verified
    if not user_data.get("email_verified", False):
        background_tasks.add_task(
            lambda: None  # _send_verification_email implementation
        )
    
    return new_user

@router.get("/{user_id}", response_model=UserProfile, summary="Get user by ID")
async def get_user(
    user_id: uuid.UUID = Path(..., description="User ID")
):
    """
    Get detailed user information by ID.
    
    User Story: As an admin or user, I can view detailed user profile information.
    
    Business Context:
    - Supports user profile viewing
    - Enables admin user management
    - Provides user data for content personalization
    """
    # Generate user details based on ID
    user_details = await _generate_user_details(user_id)
    
    if not user_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user_details

@router.put("/{user_id}", response_model=UserProfile, summary="Update user profile")
async def update_user(
    user_id: uuid.UUID,
    user_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Update user profile information.
    
    User Story: As a user, I can update my profile information including
    name, bio, preferences, and settings.
    
    Business Context:
    - Enables user self-service profile management
    - Supports multilingual profile information
    - Triggers profile validation and caching updates
    """
    # Add background tasks
    background_tasks.add_task(_update_user_cache, user_id)
    background_tasks.add_task(_log_profile_update, user_id, user_data.keys())
    
    # Get existing user data
    existing_user = await _generate_user_details(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate update permissions and data
    if "username" in user_data:
        new_username = user_data["username"]
        if new_username != existing_user.get("username"):
            # Check username uniqueness
            existing_usernames = ["admin", "root", "system", "ahmad_scholar", "fatima_student"]
            if new_username.lower() in [u.lower() for u in existing_usernames]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists"
                )
            
            # Validate username format
            if not new_username.replace("_", "").replace("-", "").isalnum():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username can only contain letters, numbers, hyphens, and underscores"
                )
            
            if len(new_username) < 3 or len(new_username) > 30:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username must be between 3 and 30 characters"
                )
    
    if "email" in user_data:
        new_email = user_data["email"]
        if new_email != existing_user.get("email"):
            # Check email uniqueness
            existing_emails = ["admin@example.com", "ahmad@example.com", "fatima@example.com"]
            if new_email.lower() in [e.lower() for e in existing_emails]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered"
                )
    
    # Merge updates with existing user data
    current_time = datetime.utcnow()
    updated_user = {**existing_user}  # Copy existing user
    
    # Apply updates
    for key, value in user_data.items():
        if key not in ["id", "created_at", "created_by", "login_count", "statistics"]:  # Protect immutable fields
            updated_user[key] = value
    
    # Update system fields
    updated_user.update({
        "updated_at": current_time.isoformat(),
        "last_active": current_time.isoformat(),
        "profile_completion": _calculate_profile_completion(updated_user)
    })
    
    # Handle email verification reset if email changed
    if "email" in user_data and user_data["email"] != existing_user.get("email"):
        updated_user["email_verified"] = False
        updated_user["account_status"] = "pending_verification"
        
        # Send verification email for new address
        background_tasks.add_task(
            lambda: None  # _send_verification_email implementation
        )
    
    # Update profile image if provided
    if "profile_image_url" in user_data:
        background_tasks.add_task(
            lambda: None  # _process_profile_image implementation
        )
    
    # Handle role changes (admin-only operation)
    if "role" in user_data and user_data["role"] != existing_user.get("role"):
        # In real implementation, check if current user has permission to change roles
        background_tasks.add_task(
            lambda: None  # _log_role_change implementation
        )
    
    # Recalculate recommendations if preferences changed
    preference_fields = ["preferred_languages", "timezone", "bio", "metadata"]
    if any(field in user_data for field in preference_fields):
        background_tasks.add_task(
            lambda: None  # _recalculate_user_recommendations implementation
        )
    
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate user")
async def deactivate_user(
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    permanent: bool = Query(False, description="Permanently delete vs soft delete")
):
    """
    Deactivate or delete user account.
    
    User Story: As an admin, I can deactivate or remove user accounts
    while maintaining data integrity.
    
    Business Context:
    - Supports user account management
    - Handles GDPR compliance requirements
    - Maintains content attribution even after user removal
    """
    background_tasks.add_task(_handle_user_deactivation, user_id, permanent)
    background_tasks.add_task(_notify_user_deactivation, user_id)
    
    return None

@router.get("/{user_id}/preferences", response_model=UserPreferences, summary="Get user preferences")
async def get_user_preferences(user_id: uuid.UUID):
    """
    Get user's content and notification preferences.
    
    User Story: As a user, I can view my current preferences and settings
    to understand how content is personalized for me.
    
    Business Context:
    - Supports personalized content delivery
    - Enables preference-based content filtering
    - Provides transparency in content algorithms
    """
    return {
        "content_types": ["video", "audio", "article", "course"],
        "categories": [
            "550e8400-e29b-41d4-a716-446655440010",
            "550e8400-e29b-41d4-a716-446655440011"
        ],
        "notification_settings": {
            "new_content": True,
            "series_updates": True,
            "social_interactions": False,
            "marketing": False
        },
        "privacy_settings": {
            "profile_visibility": "public",
            "activity_tracking": True,
            "personalized_ads": False
        },
        "content_filters": {
            "languages": ["ar", "en"],
            "difficulty_level": ["beginner", "intermediate"],
            "content_length": {"min": 0, "max": 3600}
        }
    }

@router.put("/{user_id}/preferences", response_model=UserPreferences, summary="Update user preferences")
async def update_user_preferences(
    user_id: uuid.UUID,
    preferences: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Update user's content and notification preferences.
    
    User Story: As a user, I can customize my content preferences to receive
    personalized content that matches my interests and learning level.
    
    Business Context:
    - Improves user engagement through personalization
    - Reduces irrelevant content delivery
    - Supports learning journey customization
    """
    background_tasks.add_task(_update_personalization_model, user_id, preferences)
    background_tasks.add_task(_recalculate_content_recommendations, user_id)
    
    return preferences

@router.get("/{user_id}/social-accounts", response_model=List[Dict[str, Any]], summary="Get linked social accounts")
async def get_user_social_accounts(user_id: uuid.UUID):
    """
    Get user's linked social media accounts.
    
    User Story: As a user, I can view my linked social media accounts
    and manage my cross-platform content sharing settings.
    
    Business Context:
    - Supports social media integration features
    - Enables cross-platform content sharing
    - Provides social account management interface
    """
    return [
        {
            "platform": "instagram",
            "account_id": "@ahmad_content_creator",
            "is_connected": True,
            "auto_share": True,
            "last_sync": "2024-12-07T12:00:00Z",
            "follower_count": 15420
        },
        {
            "platform": "twitter",
            "account_id": "@educational_content",
            "is_connected": True,
            "auto_share": False,
            "last_sync": "2024-12-06T18:30:00Z",
            "follower_count": 8950
        }
    ]

@router.post("/{user_id}/social-accounts", response_model=Dict[str, Any], summary="Link social media account")
async def link_social_account(
    user_id: uuid.UUID,
    social_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Link a new social media account to user profile.
    
    User Story: As a content creator, I can link my social media accounts
    to automatically share content across platforms.
    
    Business Context:
    - Expands content reach through social media
    - Enables automated content distribution
    - Supports creator monetization through multiple platforms
    """
    background_tasks.add_task(_verify_social_account, user_id, social_data)
    background_tasks.add_task(_initialize_social_sync, user_id, social_data.get("platform"))
    
    return {
        "platform": social_data.get("platform"),
        "account_id": social_data.get("account_id"),
        "is_connected": True,
        "auto_share": False,
        "last_sync": None,
        "follower_count": 0
    }

@router.delete("/{user_id}/social-accounts/{platform}", status_code=status.HTTP_204_NO_CONTENT, summary="Unlink social account")
async def unlink_social_account(
    user_id: uuid.UUID,
    platform: str,
    background_tasks: BackgroundTasks
):
    """
    Unlink social media account from user profile.
    
    User Story: As a user, I can remove social media integrations
    when I no longer want automated sharing.
    """
    background_tasks.add_task(_cleanup_social_integration, user_id, platform)
    return None

@router.get("/{user_id}/analytics", response_model=Dict[str, Any], summary="Get user analytics")
async def get_user_analytics(
    user_id: uuid.UUID,
    period: str = Query("30d", description="Analytics period (7d, 30d, 90d, 1y)"),
    metrics: Optional[List[str]] = Query(None, description="Specific metrics to include")
):
    """
    Get user engagement and activity analytics.
    
    User Story: As an admin, I can view user engagement metrics to understand
    platform usage and improve content strategy.
    
    Business Context:
    - Supports data-driven content decisions
    - Enables user engagement optimization
    - Provides insights for platform improvement
    """
    return {
        "period": period,
        "user_id": str(user_id),
        "engagement_metrics": {
            "content_views": 245,
            "content_likes": 67,
            "content_shares": 23,
            "comments_made": 15,
            "series_completed": 3,
            "learning_streak_days": 12
        },
        "content_consumption": {
            "total_watch_time_minutes": 1240,
            "favorite_categories": ["technology", "science"],
            "preferred_content_length": "10-15 minutes",
            "most_active_time": "evening"
        },
        "social_impact": {
            "content_shared": 8,
            "social_reach": 1250,
            "social_engagement": 89
        },
        "learning_progress": {
            "topics_studied": 15,
            "mastery_level": "intermediate",
            "certificates_earned": 2,
            "study_goals_achieved": 4
        }
    }

@router.post("/{user_id}/export-data", response_model=Dict[str, Any], summary="Export user data")
async def export_user_data(
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    export_type: str = Query("complete", description="Export type: basic, complete, gdpr"),
):
    """
    Export user data for GDPR compliance or user request.
    
    User Story: As a user, I can export all my data from the platform
    for backup or migration purposes.
    
    Business Context:
    - Ensures GDPR compliance
    - Supports user data portability rights
    - Enables platform migration if needed
    """
    background_tasks.add_task(_generate_user_export, user_id, export_type)
    
    return {
        "export_id": "export_" + str(uuid.uuid4()),
        "export_type": export_type,
        "status": "processing",
        "estimated_completion": "5-10 minutes",
        "notification_method": "email"
    }

# Background task functions (would be implemented in separate service layer)
async def _send_welcome_email(email: str):
    """Send welcome email to new user"""
    pass

async def _initialize_user_preferences(user_id: str):
    """Initialize default preferences for new user"""
    pass

async def _update_user_cache(user_id: uuid.UUID):
    """Update user data in cache systems"""
    pass

async def _log_profile_update(user_id: uuid.UUID, updated_fields: List[str]):
    """Log profile update for audit purposes"""
    pass

async def _handle_user_deactivation(user_id: uuid.UUID, permanent: bool):
    """Handle user deactivation process"""
    pass

async def _notify_user_deactivation(user_id: uuid.UUID):
    """Send deactivation notifications"""
    pass

async def _update_personalization_model(user_id: uuid.UUID, preferences: Dict[str, Any]):
    """Update AI personalization model with new preferences"""
    pass

async def _recalculate_content_recommendations(user_id: uuid.UUID):
    """Recalculate content recommendations based on updated preferences"""
    pass

async def _verify_social_account(user_id: uuid.UUID, social_data: Dict[str, Any]):
    """Verify social media account ownership"""
    pass

async def _initialize_social_sync(user_id: uuid.UUID, platform: str):
    """Initialize social media synchronization"""
    pass

async def _cleanup_social_integration(user_id: uuid.UUID, platform: str):
    """Clean up social media integration data"""
    pass

async def _generate_user_export(user_id: uuid.UUID, export_type: str):
    """Generate user data export file"""
    pass


# Helper functions for user operations
async def _generate_users_list(
    page: int,
    limit: int,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
    created_after: Optional[datetime] = None
) -> List[Dict]:
    """Generate realistic user list for testing purposes"""
    
    base_users = []
    base_roles = ["user", "content_creator", "moderator", "admin"]
    base_timezones = ["Asia/Riyadh", "Asia/Cairo", "Asia/Dubai", "Europe/London", "UTC"]
    
    # Generate sample users
    user_templates = [
        {
            "username": "ahmad_scholar",
            "email": "ahmad@example.com",
            "full_name": "أحمد الباحث",
            "bio": "طالب علم شرعي ومحب للقرآن الكريم",
            "role": "content_creator",
            "preferred_languages": ["ar", "en"],
            "timezone": "Asia/Riyadh"
        },
        {
            "username": "fatima_student",
            "email": "fatima@example.com", 
            "full_name": "فاطمة الطالبة",
            "bio": "طالبة في كلية الشريعة، أحب تعلم أحكام القرآن",
            "role": "user",
            "preferred_languages": ["ar"],
            "timezone": "Asia/Cairo"
        },
        {
            "username": "omar_teacher",
            "email": "omar@example.com",
            "full_name": "عمر المعلم",
            "bio": "معلم قرآن وتجويد",
            "role": "content_creator",
            "preferred_languages": ["ar", "en"],
            "timezone": "Asia/Dubai"
        },
        {
            "username": "sarah_admin",
            "email": "sarah@example.com",
            "full_name": "Sarah Administrator",
            "bio": "Platform administrator and community manager",
            "role": "admin",
            "preferred_languages": ["en", "ar"],
            "timezone": "Europe/London"
        },
        {
            "username": "ali_moderator",
            "email": "ali@example.com",
            "full_name": "علي المشرف",
            "bio": "مشرف المحتوى والمجتمع",
            "role": "moderator",
            "preferred_languages": ["ar", "en"],
            "timezone": "Asia/Riyadh"
        }
    ]
    
    # Generate more users for pagination testing
    for i, template in enumerate(user_templates):
        for j in range(3):  # Create 3 variations of each template
            user_id = str(uuid.uuid4())
            created_date = datetime.utcnow() - timedelta(days=(i * 30 + j * 10))
            last_active = datetime.utcnow() - timedelta(hours=(i * 6 + j * 2))
            
            user = {
                "id": user_id,
                "username": f"{template['username']}_{j + 1}" if j > 0 else template['username'],
                "email": template['email'].replace('@', f'_{j + 1}@') if j > 0 else template['email'],
                "full_name": template['full_name'],
                "profile_image_url": f"https://cdn.example.com/profiles/{user_id}.jpg",
                "bio": template['bio'],
                "preferred_languages": template['preferred_languages'],
                "timezone": template['timezone'],
                "role": template['role'],
                "is_active": (i + j) % 10 != 0,  # 90% active
                "email_verified": (i + j) % 20 != 0,  # 95% verified
                "created_at": created_date.isoformat() + "Z",
                "updated_at": (created_date + timedelta(days=1)).isoformat() + "Z",
                "last_active": last_active.isoformat() + "Z",
                "last_login": (last_active - timedelta(hours=1)).isoformat() + "Z",
                "login_count": (i * 10 + j * 5) + hash(user_id) % 50,
                "profile_completion": 60 + (i + j) * 5,
                "engagement_score": 50 + (i + j) * 8,
                "account_status": "active" if (i + j) % 15 != 0 else "pending_verification",
                "two_factor_enabled": (i + j) % 7 == 0,  # ~15% have 2FA
                "statistics": {
                    "content_views": (i + 1) * 100 + j * 50,
                    "content_created": (i + j) * 5 if template['role'] in ['content_creator', 'admin'] else 0,
                    "social_shares": (i + j) * 10,
                    "comments_made": (i + j) * 15
                }
            }
            
            base_users.append(user)
    
    return base_users


async def _generate_user_details(user_id: uuid.UUID) -> Optional[Dict]:
    """Generate detailed user information based on user ID"""
    
    # Simulate that some user IDs don't exist
    if str(user_id).startswith('00000000'):
        return None
    
    # Generate deterministic user based on ID
    id_hash = hash(str(user_id))
    
    user_templates = [
        {
            "username": "ahmad_scholar",
            "email": "ahmad@example.com",
            "full_name": "أحمد الباحث",
            "bio": "طالب علم شرعي ومحب للقرآن الكريم",
            "role": "content_creator"
        },
        {
            "username": "fatima_student", 
            "email": "fatima@example.com",
            "full_name": "فاطمة الطالبة",
            "bio": "طالبة في كلية الشريعة، أحب تعلم أحكام القرآن",
            "role": "user"
        },
        {
            "username": "omar_teacher",
            "email": "omar@example.com",
            "full_name": "عمر المعلم", 
            "bio": "معلم قرآن وتجويد",
            "role": "content_creator"
        },
        {
            "username": "sarah_admin",
            "email": "sarah@example.com",
            "full_name": "Sarah Administrator",
            "bio": "Platform administrator and community manager",
            "role": "admin"
        }
    ]
    
    template = user_templates[abs(id_hash) % len(user_templates)]
    created_date = datetime.utcnow() - timedelta(days=abs(id_hash) % 365)
    last_active = datetime.utcnow() - timedelta(hours=abs(id_hash) % 168)  # Within last week
    
    user_details = {
        "id": str(user_id),
        "username": template["username"],
        "email": template["email"],
        "full_name": template["full_name"],
        "profile_image_url": f"https://cdn.example.com/profiles/{user_id}.jpg",
        "bio": template["bio"],
        "preferred_languages": ["ar", "en"],
        "timezone": ["Asia/Riyadh", "Asia/Cairo", "Asia/Dubai", "UTC"][abs(id_hash) % 4],
        "role": template["role"],
        "is_active": abs(id_hash) % 20 != 0,  # 95% active
        "email_verified": abs(id_hash) % 50 != 0,  # 98% verified
        "phone_number": f"+966{5000000 + abs(id_hash) % 9999999}",
        "phone_verified": abs(id_hash) % 3 == 0,  # 33% phone verified
        "two_factor_enabled": abs(id_hash) % 10 == 0,  # 10% have 2FA
        "created_at": created_date.isoformat() + "Z",
        "updated_at": (created_date + timedelta(days=abs(id_hash) % 30)).isoformat() + "Z",
        "last_active": last_active.isoformat() + "Z",
        "last_login": (last_active - timedelta(hours=1)).isoformat() + "Z",
        "login_count": abs(id_hash) % 500 + 1,
        "profile_completion": max(60, min(100, 60 + (abs(id_hash) % 40))),
        "engagement_score": abs(id_hash) % 100,
        "account_status": "active" if abs(id_hash) % 15 != 0 else "pending_verification",
        "created_by": "system",
        "metadata": {
            "signup_source": ["web", "mobile_app", "social", "referral"][abs(id_hash) % 4],
            "referral_code": f"REF{abs(id_hash) % 10000}",
            "marketing_consent": abs(id_hash) % 3 == 0
        },
        "preferences": {
            "content_types": ["video", "audio", "article"][:(abs(id_hash) % 3) + 1],
            "categories": [str(uuid.uuid4()) for _ in range((abs(id_hash) % 5) + 1)],
            "notification_settings": {
                "new_content": True,
                "series_updates": abs(id_hash) % 2 == 0,
                "social_interactions": abs(id_hash) % 3 == 0,
                "marketing": abs(id_hash) % 4 == 0,
                "email_notifications": True,
                "push_notifications": abs(id_hash) % 2 == 0
            },
            "privacy_settings": {
                "profile_visibility": "public" if abs(id_hash) % 4 != 0 else "private",
                "activity_tracking": abs(id_hash) % 5 != 0,
                "personalized_ads": abs(id_hash) % 3 == 0,
                "data_sharing": abs(id_hash) % 6 == 0
            },
            "content_filters": {
                "languages": ["ar", "en"] if abs(id_hash) % 2 == 0 else ["ar"],
                "difficulty_level": ["beginner", "intermediate", "advanced"][:(abs(id_hash) % 3) + 1],
                "content_length": {
                    "min": 0,
                    "max": [1800, 3600, 7200][abs(id_hash) % 3]  # 30min, 1hr, 2hr
                }
            }
        },
        "statistics": {
            "content_views": abs(id_hash) % 1000 + 100,
            "content_created": (abs(id_hash) % 50) if template["role"] in ["content_creator", "admin"] else 0,
            "social_shares": abs(id_hash) % 200,
            "comments_made": abs(id_hash) % 100,
            "likes_given": abs(id_hash) % 500,
            "bookmarks": abs(id_hash) % 150,
            "series_completed": abs(id_hash) % 20,
            "certificates_earned": abs(id_hash) % 10,
            "total_watch_time_minutes": abs(id_hash) % 10000 + 500
        },
        "social_accounts": [
            {
                "platform": "instagram",
                "account_id": f"@{template['username']}_insta",
                "is_connected": abs(id_hash) % 3 == 0,
                "follower_count": abs(id_hash) % 50000
            },
            {
                "platform": "twitter", 
                "account_id": f"@{template['username']}_tw",
                "is_connected": abs(id_hash) % 4 == 0,
                "follower_count": abs(id_hash) % 20000
            }
        ] if abs(id_hash) % 2 == 0 else []
    }
    
    return user_details


def _calculate_profile_completion(user_data: dict) -> int:
    """Calculate profile completion percentage based on filled fields"""
    
    total_fields = 15
    completed_fields = 0
    
    # Required fields
    if user_data.get("username"):
        completed_fields += 1
    if user_data.get("email"):
        completed_fields += 1
    if user_data.get("full_name"):
        completed_fields += 1
    
    # Optional but important fields
    if user_data.get("bio"):
        completed_fields += 2
    if user_data.get("profile_image_url"):
        completed_fields += 2
    if user_data.get("phone_number"):
        completed_fields += 1
    if user_data.get("timezone") and user_data.get("timezone") != "UTC":
        completed_fields += 1
    if user_data.get("preferred_languages") and len(user_data.get("preferred_languages", [])) > 0:
        completed_fields += 1
    
    # Preference fields
    preferences = user_data.get("preferences", {})
    if preferences.get("content_types"):
        completed_fields += 1
    if preferences.get("categories"):
        completed_fields += 1
    if preferences.get("notification_settings"):
        completed_fields += 1
    if preferences.get("privacy_settings"):
        completed_fields += 1
    
    # Verification fields
    if user_data.get("email_verified"):
        completed_fields += 1
    if user_data.get("phone_verified"):
        completed_fields += 1
    
    return min(100, int((completed_fields / total_fields) * 100))