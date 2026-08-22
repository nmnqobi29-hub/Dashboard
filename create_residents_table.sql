

CREATE TABLE IF NOT EXISTS residents (
    id SERIAL PRIMARY KEY,             
    student_number BIGINT NOT NULL,    
    student_name TEXT NOT NULL,
    room_number TEXT NOT NULL,
    academic_year TEXT NOT NULL,       
    lease_status TEXT NOT NULL,        
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast lookups by student number (even though it's not unique yet)
CREATE INDEX IF NOT EXISTS idx_residents_student_number ON residents (student_number);

-- Index for fast lookups by room (useful for occupancy checks)
CREATE INDEX IF NOT EXISTS idx_residents_room_number ON residents (room_number);

-- Once the duplicate student_number (22297135) is resolved, run this to enforce uniqueness:
-- ALTER TABLE residents ADD CONSTRAINT residents_student_number_unique UNIQUE (student_number);
