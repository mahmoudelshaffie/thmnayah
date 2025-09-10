# User Management Service

## Service Overview

**Responsibility**: Authentication, authorization, and user profiles management  
**Domain**: Identity and access management  
**Data**: User profiles, roles, permissions, sessions  
**Users**: All system users (internal & external)

## Core Features

### User Authentication
- Multi-factor authentication (MFA) support
- OAuth2/OIDC integration with Keycloak
- JWT token management and validation
- Session management and timeout handling
- Password policies and security enforcement

### Role-Based Access Control (RBAC)
- Hierarchical role management
- Fine-grained permission system
- Resource-based access control
- Dynamic permission assignment
- Role inheritance and composition

### User Profile Management
- Comprehensive user profile data
- Profile customization and preferences
- Multi-language profile support (Arabic/English)
- User activity tracking and history
- Profile picture and media management

### Session Management
- Secure session creation and validation
- Cross-device session synchronization
- Session timeout and renewal
- Concurrent session limits
- Session analytics and monitoring

### Integration with Keycloak
- Single Sign-On (SSO) capabilities
- Federated identity management
- External identity provider integration
- User import and synchronization
- Advanced authentication flows

---

## Technical Specifications

### Tech Stack
```yaml
Runtime: Python 3.11+
Framework: FastAPI 0.104+
Database: PostgreSQL 15+ (primary), Redis 7+ (sessions)
Authentication: Keycloak 22+
Message Queue: NATS 2.10+
Caching: Redis 7+
Monitoring: Prometheus + Grafana
Security: JWT, bcrypt, python-jose
Testing: pytest, asyncio-compatible
```

### Dependencies
```yaml
Internal Services:
  - Analytics Service (user activity tracking)
  - Notification Service (user notifications)
  - Content Management Service (user-content relationships)

External Services:
  - Keycloak (identity provider)
  - PostgreSQL (user data)
  - Redis (session storage, caching)
  - NATS (event messaging)
  - AWS SES (email notifications)
```

---

## Data Models

### User Model
```python
class User(BaseModel):
    id: str = Field(..., description="Unique user identifier (UUID)")
    keycloak_id: Optional[str] = Field(None, description="Keycloak user ID")
    
    # Basic Information
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="User email address")
    email_verified: bool = Field(False, description="Email verification status")
    
    # Profile Information
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    display_name: Optional[str] = Field(None, max_length=100, description="Public display name")
    
    # Profile Details
    bio: Optional[Dict[str, str]] = Field(None, description="User biography (ar/en)")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    website_url: Optional[str] = Field(None, description="Personal website")
    
    # Preferences
    language: str = Field("en", description="Preferred language (ar/en)")
    timezone: str = Field("UTC", description="User timezone")
    theme: str = Field("light", description="UI theme preference")
    
    # Status
    status: UserStatus = Field(UserStatus.ACTIVE, description="User account status")
    is_verified: bool = Field(False, description="User verification status")
    is_staff: bool = Field(False, description="Staff member flag")
    is_superuser: bool = Field(False, description="Superuser flag")
    
    # Security
    password_changed_at: Optional[datetime] = Field(None, description="Last password change")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    failed_login_attempts: int = Field(0, description="Failed login attempt count")
    locked_until: Optional[datetime] = Field(None, description="Account lock expiry")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default={}, description="Additional user metadata")

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"
```

### Role Model
```python
class Role(BaseModel):
    id: str = Field(..., description="Unique role identifier")
    name: str = Field(..., min_length=2, max_length=100, description="Role name")
    display_name: Dict[str, str] = Field(..., description="Display name (ar/en)")
    description: Dict[str, str] = Field(..., description="Role description (ar/en)")
    
    # Hierarchy
    parent_role_id: Optional[str] = Field(None, description="Parent role for hierarchy")
    level: int = Field(0, description="Role level in hierarchy")
    
    # Configuration
    is_system_role: bool = Field(False, description="System-defined role flag")
    is_assignable: bool = Field(True, description="Can be assigned to users")
    
    # Permissions
    permissions: List[str] = Field(default=[], description="List of permission IDs")
    
    # Status
    is_active: bool = Field(True, description="Role active status")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default={}, description="Role metadata")
```

### Permission Model
```python
class Permission(BaseModel):
    id: str = Field(..., description="Unique permission identifier")
    name: str = Field(..., description="Permission name (e.g., 'content:create')")
    display_name: Dict[str, str] = Field(..., description="Display name (ar/en)")
    description: Dict[str, str] = Field(..., description="Permission description")
    
    # Classification
    resource: str = Field(..., description="Resource type (content, user, etc.)")
    action: str = Field(..., description="Action type (create, read, update, delete)")
    scope: PermissionScope = Field(PermissionScope.GLOBAL, description="Permission scope")
    
    # Grouping
    category: str = Field(..., description="Permission category")
    group: Optional[str] = Field(None, description="Permission group")
    
    # Status
    is_system_permission: bool = Field(False, description="System permission flag")
    is_active: bool = Field(True, description="Permission active status")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PermissionScope(str, Enum):
    GLOBAL = "global"
    ORGANIZATION = "organization"
    PROJECT = "project"
    USER = "user"
```

### User Role Assignment Model
```python
class UserRole(BaseModel):
    id: str = Field(..., description="Unique assignment identifier")
    user_id: str = Field(..., description="User identifier")
    role_id: str = Field(..., description="Role identifier")
    
    # Assignment Details
    assigned_by: str = Field(..., description="User who made the assignment")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Scope and Context
    scope: Optional[str] = Field(None, description="Assignment scope (e.g., project_id)")
    context: Dict[str, Any] = Field(default={}, description="Assignment context")
    
    # Validity
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = Field(None, description="Assignment expiry")
    
    # Status
    is_active: bool = Field(True, description="Assignment active status")
    
    # Timestamps
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Session Model
```python
class UserSession(BaseModel):
    id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Session Details
    token: str = Field(..., description="Session token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    
    # Device Information
    device_id: Optional[str] = Field(None, description="Device identifier")
    device_type: str = Field("web", description="Device type")
    user_agent: Optional[str] = Field(None, description="User agent string")
    ip_address: str = Field(..., description="Client IP address")
    
    # Location
    country: Optional[str] = Field(None, description="Country from IP")
    city: Optional[str] = Field(None, description="City from IP")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Session expiry time")
    
    # Status
    is_active: bool = Field(True, description="Session active status")
    
    # Security
    login_method: str = Field("password", description="Login method used")
    mfa_verified: bool = Field(False, description="MFA verification status")
```

---

## API Endpoints

### User Management
```python
# User CRUD
POST   /api/v1/users                     # Create user (registration)
GET    /api/v1/users                     # List users (admin only)
GET    /api/v1/users/{user_id}           # Get user profile
PUT    /api/v1/users/{user_id}           # Update user profile
DELETE /api/v1/users/{user_id}           # Delete user account
PATCH  /api/v1/users/{user_id}/status    # Update user status

# User Profile
GET    /api/v1/users/me                  # Get current user profile
PUT    /api/v1/users/me                  # Update current user profile
POST   /api/v1/users/me/avatar           # Upload profile picture
DELETE /api/v1/users/me/avatar           # Remove profile picture

# User Verification
POST   /api/v1/users/{user_id}/verify    # Send verification email
PUT    /api/v1/users/verify/{token}      # Verify user account
POST   /api/v1/users/resend-verification # Resend verification
```

### Authentication
```python
# Authentication
POST   /api/v1/auth/login              # User login
POST   /api/v1/auth/logout             # User logout
POST   /api/v1/auth/refresh            # Refresh access token
POST   /api/v1/auth/forgot-password    # Forgot password request
POST   /api/v1/auth/reset-password     # Reset password with token
POST   /api/v1/auth/change-password    # Change password (authenticated)

# Multi-Factor Authentication
POST   /api/v1/auth/mfa/enable         # Enable MFA
POST   /api/v1/auth/mfa/disable        # Disable MFA
POST   /api/v1/auth/mfa/verify         # Verify MFA token
GET    /api/v1/auth/mfa/qr-code        # Get MFA QR code

# OAuth/Keycloak
GET    /api/v1/auth/oauth/authorize    # OAuth authorization
POST   /api/v1/auth/oauth/token        # OAuth token exchange
GET    /api/v1/auth/oauth/userinfo     # Get OAuth user info
POST   /api/v1/auth/oauth/logout       # OAuth logout
```

### Role Management
```python
# Role CRUD
POST   /api/v1/roles                   # Create role
GET    /api/v1/roles                   # List roles
GET    /api/v1/roles/{role_id}         # Get role details
PUT    /api/v1/roles/{role_id}         # Update role
DELETE /api/v1/roles/{role_id}         # Delete role

# Role Permissions
GET    /api/v1/roles/{role_id}/permissions    # Get role permissions
PUT    /api/v1/roles/{role_id}/permissions    # Update role permissions
POST   /api/v1/roles/{role_id}/permissions    # Add permissions to role
DELETE /api/v1/roles/{role_id}/permissions/{permission_id} # Remove permission

# User Role Assignment
GET    /api/v1/users/{user_id}/roles          # Get user roles
POST   /api/v1/users/{user_id}/roles          # Assign role to user
DELETE /api/v1/users/{user_id}/roles/{role_id} # Remove role from user
```

### Permission Management
```python
# Permission CRUD
POST   /api/v1/permissions                      # Create permission
GET    /api/v1/permissions                      # List permissions
GET    /api/v1/permissions/{permission_id}      # Get permission details
PUT    /api/v1/permissions/{permission_id}      # Update permission
DELETE /api/v1/permissions/{permission_id}      # Delete permission

# Permission Checking
GET    /api/v1/users/{user_id}/permissions      # Get user permissions
POST   /api/v1/auth/check-permission            # Check user permission
GET    /api/v1/permissions/by-resource/{resource} # Get permissions by resource
```

### Session Management
```python
# Session Management
GET    /api/v1/sessions                  # Get user sessions
GET    /api/v1/sessions/{session_id}     # Get session details
DELETE /api/v1/sessions/{session_id}     # Revoke specific session
DELETE /api/v1/sessions                  # Revoke all sessions
GET    /api/v1/sessions/active           # Get active sessions

# Session Information
GET    /api/v1/auth/session-info         # Get current session info
POST   /api/v1/auth/extend-session       # Extend session duration
GET    /api/v1/users/me/login-history    # Get user login history
```

---

## Core Workflows

### User Registration Workflow
```python
async def register_user_workflow(registration_data: UserRegistrationRequest) -> UserRegistrationResponse:
    """Complete user registration with validation and setup"""
    
    # 1. Validate registration data
    await validate_registration_data(registration_data)
    
    # 2. Check if user already exists
    existing_user = await find_user_by_email(registration_data.email)
    if existing_user:
        raise UserAlreadyExistsError("User with this email already exists")
    
    # 3. Create user in Keycloak
    keycloak_user = await create_keycloak_user(registration_data)
    
    # 4. Create user in local database
    user = await create_user({
        **registration_data.dict(),
        "keycloak_id": keycloak_user.id,
        "status": UserStatus.PENDING_VERIFICATION,
        "password": await hash_password(registration_data.password)
    })
    
    # 5. Assign default roles
    default_roles = await get_default_user_roles()
    for role in default_roles:
        await assign_user_role(user.id, role.id, system_user_id)
    
    # 6. Send verification email
    verification_token = await create_verification_token(user.id)
    await send_verification_email(user.email, verification_token)
    
    # 7. Log registration event
    await log_user_event(user.id, "user_registered", {
        "registration_method": "email",
        "ip_address": registration_data.ip_address
    })
    
    # 8. Send welcome notification
    await send_welcome_notification(user)
    
    return UserRegistrationResponse(
        user_id=user.id,
        email=user.email,
        status="pending_verification",
        verification_sent=True
    )
```

### Authentication Workflow
```python
async def authenticate_user_workflow(credentials: LoginCredentials) -> AuthenticationResponse:
    """Authenticate user with comprehensive security checks"""
    
    # 1. Rate limiting check
    await check_login_rate_limit(credentials.email, credentials.ip_address)
    
    # 2. Find user by email/username
    user = await find_user_for_login(credentials.email)
    if not user:
        await log_failed_login_attempt(credentials.email, "user_not_found")
        raise InvalidCredentialsError()
    
    # 3. Check account status
    if user.status != UserStatus.ACTIVE:
        await log_failed_login_attempt(user.id, "account_inactive")
        raise AccountInactiveError(f"Account status: {user.status}")
    
    # 4. Check account lock
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise AccountLockedError(f"Account locked until {user.locked_until}")
    
    # 5. Verify password
    if not await verify_password(credentials.password, user.password_hash):
        await handle_failed_login(user.id)
        raise InvalidCredentialsError()
    
    # 6. Check MFA if enabled
    if user.mfa_enabled:
        if not credentials.mfa_token:
            return AuthenticationResponse(
                status="mfa_required",
                mfa_methods=["totp", "sms"]
            )
        
        if not await verify_mfa_token(user.id, credentials.mfa_token):
            await handle_failed_login(user.id)
            raise InvalidMFATokenError()
    
    # 7. Create session
    session = await create_user_session({
        "user_id": user.id,
        "device_type": credentials.device_type,
        "user_agent": credentials.user_agent,
        "ip_address": credentials.ip_address,
        "login_method": "password",
        "mfa_verified": user.mfa_enabled
    })
    
    # 8. Generate tokens
    access_token = await generate_access_token(user, session)
    refresh_token = await generate_refresh_token(session)
    
    # 9. Update user login info
    await update_user_login_info(user.id, credentials.ip_address)
    
    # 10. Reset failed login attempts
    await reset_failed_login_attempts(user.id)
    
    # 11. Log successful login
    await log_user_event(user.id, "user_login", {
        "session_id": session.id,
        "ip_address": credentials.ip_address,
        "device_type": credentials.device_type
    })
    
    return AuthenticationResponse(
        status="success",
        access_token=access_token,
        refresh_token=refresh_token,
        user=user.dict(exclude={"password_hash"}),
        session_id=session.id
    )
```

### Permission Checking Workflow
```python
async def check_user_permission_workflow(
    user_id: str, 
    permission: str, 
    resource_id: Optional[str] = None
) -> PermissionCheckResult:
    """Check if user has specific permission with caching"""
    
    # 1. Check cache first
    cache_key = f"user_permissions:{user_id}:{permission}:{resource_id or 'global'}"
    cached_result = await get_cached_permission(cache_key)
    if cached_result is not None:
        return PermissionCheckResult(allowed=cached_result, cached=True)
    
    # 2. Get user roles
    user_roles = await get_user_active_roles(user_id)
    if not user_roles:
        await cache_permission_result(cache_key, False, ttl=300)
        return PermissionCheckResult(allowed=False, reason="no_roles")
    
    # 3. Check superuser status
    user = await get_user(user_id)
    if user.is_superuser:
        await cache_permission_result(cache_key, True, ttl=600)
        return PermissionCheckResult(allowed=True, reason="superuser")
    
    # 4. Get all permissions from roles
    all_permissions = []
    for role in user_roles:
        role_permissions = await get_role_permissions(role.id)
        all_permissions.extend(role_permissions)
    
    # 5. Check permission match
    has_permission = False
    for perm in all_permissions:
        if perm.name == permission:
            # Check scope if resource_id provided
            if resource_id and perm.scope != PermissionScope.GLOBAL:
                # Implement resource-specific permission logic
                has_permission = await check_resource_permission(
                    user_id, perm, resource_id
                )
            else:
                has_permission = True
            break
    
    # 6. Cache result
    await cache_permission_result(cache_key, has_permission, ttl=300)
    
    # 7. Log permission check if denied
    if not has_permission:
        await log_permission_denied(user_id, permission, resource_id)
    
    return PermissionCheckResult(
        allowed=has_permission,
        permission=permission,
        resource_id=resource_id
    )
```

### Session Management Workflow
```python
async def manage_user_sessions_workflow(user_id: str, action: str, session_id: Optional[str] = None):
    """Manage user sessions (revoke, cleanup, etc.)"""
    
    # 1. Get user sessions
    user_sessions = await get_user_sessions(user_id)
    
    if action == "revoke_all":
        # Revoke all user sessions
        for session in user_sessions:
            await revoke_session(session.id)
        
        # Update Keycloak sessions
        await revoke_keycloak_sessions(user_id)
        
        # Clear cached permissions
        await clear_user_permission_cache(user_id)
        
        await log_user_event(user_id, "all_sessions_revoked", {
            "session_count": len(user_sessions)
        })
    
    elif action == "revoke_session" and session_id:
        # Revoke specific session
        session = await get_session(session_id)
        if session and session.user_id == user_id:
            await revoke_session(session_id)
            
            # Clear cached permissions for this session
            await clear_session_permission_cache(session_id)
            
            await log_user_event(user_id, "session_revoked", {
                "session_id": session_id
            })
    
    elif action == "cleanup_expired":
        # Clean up expired sessions
        expired_sessions = [s for s in user_sessions if s.expires_at < datetime.utcnow()]
        for session in expired_sessions:
            await delete_expired_session(session.id)
        
        if expired_sessions:
            await log_user_event(user_id, "expired_sessions_cleaned", {
                "cleaned_count": len(expired_sessions)
            })
    
    elif action == "limit_check":
        # Enforce concurrent session limits
        max_sessions = await get_user_session_limit(user_id)
        if len(user_sessions) > max_sessions:
            # Remove oldest sessions
            sorted_sessions = sorted(user_sessions, key=lambda s: s.last_activity_at)
            sessions_to_remove = sorted_sessions[:-max_sessions]
            
            for session in sessions_to_remove:
                await revoke_session(session.id)
            
            await log_user_event(user_id, "sessions_limited", {
                "removed_count": len(sessions_to_remove),
                "limit": max_sessions
            })
```

---

## Performance Requirements

### Response Time Targets
```yaml
Authentication Operations:
  - User login: <200ms (95th percentile)
  - Token validation: <50ms (95th percentile)
  - Token refresh: <100ms (95th percentile)
  - Logout: <100ms (95th percentile)

User Management:
  - User profile retrieval: <100ms (95th percentile)
  - User profile update: <200ms (95th percentile)
  - User creation: <300ms (95th percentile)
  - Password change: <200ms (95th percentile)

Permission Checking:
  - Permission check (cached): <10ms (95th percentile)
  - Permission check (uncached): <50ms (95th percentile)
  - Role assignment: <150ms (95th percentile)
  - Permission update: <100ms (95th percentile)

Session Management:
  - Session creation: <100ms (95th percentile)
  - Session validation: <50ms (95th percentile)
  - Session revocation: <100ms (95th percentile)
  - Session cleanup: <500ms (background)
```

### Throughput Targets
```yaml
Authentication:
  - Login requests: 500 requests/second
  - Token validation: 5000 requests/second
  - Token refresh: 200 requests/second
  - Logout requests: 300 requests/second

Permission Checks:
  - Permission validation: 10000 requests/second (with caching)
  - Role-based checks: 1000 requests/second
  - Resource permission checks: 500 requests/second

User Operations:
  - User profile requests: 1000 requests/second
  - User updates: 100 requests/second
  - User creation: 50 requests/second

Session Management:
  - Session operations: 1000 requests/second
  - Concurrent active sessions: 10000 sessions
  - Session cleanup: 1000 sessions/minute (background)
```

### Data Scale Expectations
```yaml
User Data:
  - Total users: Up to 100,000 users
  - Active users: Up to 10,000 concurrent
  - User sessions: Up to 50,000 active sessions
  - Roles: Up to 100 roles
  - Permissions: Up to 1,000 permissions

Operational Scale:
  - Daily logins: 50,000 login attempts
  - Daily permission checks: 1 million checks
  - Daily user operations: 10,000 operations
  - Session cleanup: 10,000 sessions/day
```

---

## Integration Points

### Internal Service Integration
```yaml
Content Management Service:
  - User-content ownership validation
  - Content access permission checks
  - User activity tracking
  - Content creation authorization

Analytics Service:
  - User behavior tracking
  - Login/logout events
  - Permission usage analytics
  - Security event logging

Notification Service:
  - User registration notifications
  - Security alert notifications
  - Password change confirmations
  - Account status updates

Search & Discovery Service:
  - User preference integration
  - Personalized search results
  - User activity influence on recommendations
```

### External Service Integration
```yaml
Keycloak Integration:
  - User identity management
  - SSO capabilities
  - OAuth2/OIDC flows
  - External identity providers
  - Advanced authentication features

Database Integration:
  - PostgreSQL (user data, roles, permissions)
  - Redis (sessions, caching, rate limiting)

Email Integration:
  - AWS SES (transactional emails)
  - Email verification
  - Password reset emails
  - Security notifications

Monitoring Integration:
  - Security event logging
  - Failed login monitoring
  - Performance metrics
  - Audit trail maintenance
```

### Event Publishing
```yaml
Authentication Events:
  - user.login
  - user.logout
  - user.login_failed
  - user.password_changed
  - user.mfa_enabled
  - user.mfa_disabled
  - session.created
  - session.revoked

User Management Events:
  - user.created
  - user.updated
  - user.deleted
  - user.verified
  - user.suspended
  - user.reactivated
  - profile.updated
  - avatar.updated

Permission Events:
  - role.assigned
  - role.unassigned
  - role.created
  - role.updated
  - permission.granted
  - permission.denied
  - permission.updated

Security Events:
  - account.locked
  - account.unlocked
  - suspicious.activity
  - security.breach
  - mfa.failed
  - password.reset
```

---

## Security & Compliance

### Authentication Security
```yaml
Password Security:
  - Minimum 8 characters with complexity requirements
  - Bcrypt hashing with minimum 12 rounds
  - Password history enforcement (last 5 passwords)
  - Password expiration policy (90 days for staff)
  - Breach password checking integration

Session Security:
  - Secure HTTP-only session cookies
  - JWT tokens with short expiration (15 minutes)
  - Refresh token rotation
  - Session fixation protection
  - Concurrent session limits

Account Security:
  - Account lockout after 5 failed attempts
  - Progressive lockout timeouts
  - Account verification requirements
  - Suspicious activity detection
  - IP-based access controls
```

### Authorization Security
```yaml
Permission Model:
  - Principle of least privilege
  - Role-based access control
  - Resource-level permissions
  - Time-limited role assignments
  - Regular permission audits

Access Control:
  - API endpoint protection
  - Resource ownership validation
  - Cross-tenant isolation
  - Administrative action logging
  - Privilege escalation monitoring
```

### Data Protection
```yaml
Personal Data:
  - GDPR compliance for user data
  - Data encryption at rest and in transit
  - Data retention policies
  - Right to be forgotten implementation
  - Data export capabilities

Privacy Controls:
  - User consent management
  - Privacy preference settings
  - Data sharing controls
  - Activity tracking opt-out
  - Communication preferences
```

### Audit and Compliance
```yaml
Audit Logging:
  - All authentication events
  - Permission changes and checks
  - Administrative actions
  - Data access and modifications
  - Security events and incidents

Compliance Features:
  - GDPR data protection
  - SOC 2 compliance preparation
  - Security incident response
  - Regular security assessments
  - Compliance reporting tools
```

This comprehensive User Management Service specification provides secure, scalable, and compliant user identity and access management for the thmnayah platform.