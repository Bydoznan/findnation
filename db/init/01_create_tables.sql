-- 01_create_tables.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS found_items (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  title VARCHAR(150) NOT NULL,
  category VARCHAR(50) NOT NULL,
  dominant_color VARCHAR(30) NOT NULL,
  description TEXT,
  distinctive_marks TEXT,
  location_found TEXT NOT NULL,
  date_found DATE NOT NULL DEFAULT CURRENT_DATE,
  voivodeship VARCHAR(50) NOT NULL,
  reporting_entity VARCHAR(100) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','returned','archived'))
);

CREATE INDEX IF NOT EXISTS idx_voivodeship ON found_items(voivodeship);
CREATE INDEX IF NOT EXISTS idx_date_found ON found_items(date_found);
CREATE INDEX IF NOT EXISTS idx_category ON found_items(category);
