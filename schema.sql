-- Supabase Schema for GoodNotes Pipeline

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: subjects (e.g. Maths, Physics, CS)
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#3B82F6',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Table: notes (One record per GoodNotes lecture/file)
CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    subject_name TEXT,
    school_name TEXT DEFAULT 'Général',
    title TEXT NOT NULL,
    gdrive_file_id TEXT UNIQUE NOT NULL,
    summary TEXT,
    full_transcription TEXT,
    pdf_url TEXT,
    page_count INT DEFAULT 0,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Table: note_pages (Per page details, images and OCR transcripts)
CREATE TABLE IF NOT EXISTS note_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    image_url TEXT,
    transcription TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Row Level Security (RLS) policies
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE note_pages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to subjects" ON subjects FOR SELECT USING (true);
CREATE POLICY "Allow public read access to notes" ON notes FOR SELECT USING (true);
CREATE POLICY "Allow public read access to note_pages" ON note_pages FOR SELECT USING (true);

-- Allow service role full access
CREATE POLICY "Allow full access to service role on subjects" ON subjects FOR ALL USING (true);
CREATE POLICY "Allow full access to service role on notes" ON notes FOR ALL USING (true);
CREATE POLICY "Allow full access to service role on note_pages" ON note_pages FOR ALL USING (true);
