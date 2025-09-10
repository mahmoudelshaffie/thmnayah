"""Create categories table

Revision ID: 001_categories
Revises: 
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

# revision identifiers
revision = '001_categories'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create categories table with hierarchical support and multilingual fields"""
    
    # Create CategoryType enum
    category_type_enum = sa.Enum(
        'TOPIC', 'FORMAT', 'AUDIENCE', 'LANGUAGE', 'SERIES_TYPE',
        name='categorytype'
    )
    
    # Create CategoryVisibility enum
    category_visibility_enum = sa.Enum(
        'PUBLIC', 'PRIVATE', 'RESTRICTED',
        name='categoryvisibility'
    )
    
    # Create the categories table
    op.create_table(
        'categories',
        
        # Primary key
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        
        # Multilingual content fields (JSON)
        sa.Column('name', JSONB, nullable=False, 
                 comment='Category name in multiple languages (language_code -> text)'),
        sa.Column('description', JSONB, nullable=True,
                 comment='Category description in multiple languages'),
        sa.Column('slug', JSONB, nullable=True,
                 comment='URL-friendly slugs in multiple languages'),
        
        # Category classification
        sa.Column('category_type', category_type_enum, 
                 nullable=False, default='TOPIC',
                 comment='Type of category (topic, format, audience, etc.)'),
        
        # Hierarchical structure
        sa.Column('parent_id', UUID(as_uuid=True), 
                 sa.ForeignKey('categories.id', ondelete='CASCADE'),
                 nullable=True,
                 comment='Parent category for hierarchical structure'),
        sa.Column('level', sa.Integer, nullable=False, default=0,
                 comment='Hierarchy level (0 = root)'),
        sa.Column('path', sa.String(1000), nullable=False,
                 comment='Full hierarchical path (e.g., /sciences/technology)'),
        
        # Status and visibility
        sa.Column('is_active', sa.Boolean, nullable=False, default=True,
                 comment='Whether category is active and visible'),
        sa.Column('visibility', category_visibility_enum,
                 nullable=False, default='public',
                 comment='Category visibility level'),
        
        # Display customization
        sa.Column('icon_url', sa.String(500), nullable=True,
                 comment='URL to category icon image'),
        sa.Column('banner_url', sa.String(500), nullable=True,
                 comment='URL to category banner image'),
        sa.Column('color_scheme', sa.String(7), nullable=True,
                 comment='Category theme color (hex code)'),
        sa.Column('sort_order', sa.Integer, nullable=False, default=0,
                 comment='Sort order within parent category'),
        
        # Content statistics (denormalized for performance)
        sa.Column('content_count', sa.Integer, nullable=False, default=0,
                 comment='Number of direct content items'),
        sa.Column('subcategory_count', sa.Integer, nullable=False, default=0,
                 comment='Number of direct subcategories'),
        sa.Column('total_content_count', sa.Integer, nullable=False, default=0,
                 comment='Total content count including subcategories'),
        
        # SEO fields (multilingual JSON)
        sa.Column('seo_title', JSONB, nullable=True,
                 comment='SEO-optimized title in multiple languages'),
        sa.Column('seo_description', JSONB, nullable=True,
                 comment='SEO meta description in multiple languages'),
        sa.Column('seo_keywords', JSONB, nullable=True,
                 comment='SEO keywords/tags array'),
        
        # Extensible metadata
        sa.Column('_metadata', JSONB, nullable=True,
                 comment='Additional category metadata'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, 
                 server_default=sa.func.now()),
        sa.Column('created_by', sa.String, nullable=True),

        sa.Column('updated_at', sa.DateTime, nullable=False,
                 server_default=sa.func.now(), onupdate=sa.func.now()),

        sa.Column('updated_by', sa.String, nullable=True),

        sa.Column('version', sa.Integer, nullable=False, default=1),
        
        # Constraints
        sa.CheckConstraint('id != parent_id', name='check_no_self_parent'),
        sa.CheckConstraint('level >= 0', name='check_valid_level'),
        sa.CheckConstraint("path LIKE '/%'", name='check_path_format'),
        sa.CheckConstraint(
            "color_scheme IS NULL OR color_scheme ~ '^#[0-9A-Fa-f]{6}$'",
            name='check_color_scheme_format'
        )
    )
    
    # Create indexes for performance
    
    # Basic lookup indexes
    op.create_index('idx_categories_id', 'categories', ['id'])
    op.create_index('idx_categories_parent_id', 'categories', ['parent_id'])
    op.create_index('idx_categories_level', 'categories', ['level'])
    op.create_index('idx_categories_is_active', 'categories', ['is_active'])
    op.create_index('idx_categories_category_type', 'categories', ['category_type'])
    op.create_index('idx_categories_visibility', 'categories', ['visibility'])
    
    # Composite indexes for common queries
    op.create_index('idx_categories_parent_level', 'categories', ['parent_id', 'level'])
    op.create_index('idx_categories_type_active', 'categories', ['category_type', 'is_active'])
    op.create_index('idx_categories_visibility_active', 'categories', ['visibility', 'is_active'])
    
    # Path-based index for hierarchical queries
    op.create_index('idx_categories_path', 'categories', ['path'])
    op.create_index(
        'idx_categories_path_prefix', 
        'categories', 
        ['path'], 
        postgresql_ops={'path': 'text_pattern_ops'}
    )
    
    # JSON field indexes for multilingual search (PostgreSQL specific)
    op.create_index(
        'idx_categories_name_gin', 
        'categories', 
        ['name'], 
        postgresql_using='gin'
    )
    op.create_index(
        'idx_categories_description_gin', 
        'categories', 
        ['description'],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_categories_slug_gin',
        'categories',
        ['slug'],
        postgresql_using='gin'
    )
    
    # Sort order index for ordering within parent
    op.create_index(
        'idx_categories_parent_sort_order',
        'categories',
        ['parent_id', 'sort_order']
    )


def downgrade():
    """Drop categories table and related objects"""
    
    # Drop all indexes
    op.drop_index('idx_categories_parent_sort_order', 'categories')
    op.drop_index('idx_categories_slug_gin', 'categories')
    op.drop_index('idx_categories_description_gin', 'categories')
    op.drop_index('idx_categories_name_gin', 'categories')
    op.drop_index('idx_categories_path_prefix', 'categories')
    op.drop_index('idx_categories_path', 'categories')
    op.drop_index('idx_categories_visibility_active', 'categories')
    op.drop_index('idx_categories_type_active', 'categories')
    op.drop_index('idx_categories_parent_level', 'categories')
    op.drop_index('idx_categories_visibility', 'categories')
    op.drop_index('idx_categories_category_type', 'categories')
    op.drop_index('idx_categories_is_active', 'categories')
    op.drop_index('idx_categories_level', 'categories')
    op.drop_index('idx_categories_parent_id', 'categories')
    op.drop_index('idx_categories_id', 'categories')
    
    # Drop table
    op.drop_table('categories')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS categoryvisibility CASCADE')
    op.execute('DROP TYPE IF EXISTS categorytype CASCADE')