-- Create database tables if they do not exist
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    user_prompt TEXT NOT NULL,
    requirements JSONB NOT NULL DEFAULT '{}'::jsonb,
    components JSONB NOT NULL DEFAULT '[]'::jsonb,
    bom JSONB NOT NULL DEFAULT '[]'::jsonb,
    wiring_diagram TEXT NOT NULL DEFAULT '',
    firmware TEXT NOT NULL DEFAULT '',
    final_report TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
