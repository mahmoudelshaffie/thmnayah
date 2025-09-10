-- Database initialization script for CMS
-- Creates necessary extensions for the CMS system

-- Enable UUID extension for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for full-text search and similarity matching
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enable btree_gin for optimized JSON indexing
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Enable unaccent for accent-insensitive searches (useful for Arabic text)
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create a function to generate slugs (useful for categories)
CREATE OR REPLACE FUNCTION generate_slug(input_text TEXT) 
RETURNS TEXT AS $$
BEGIN
    RETURN lower(
        regexp_replace(
            regexp_replace(
                unaccent(input_text), 
                '[^a-zA-Z0-9\s\-_]', '', 'g'
            ), 
            '\s+', '-', 'g'
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;