-- Create students table
CREATE TABLE IF NOT EXISTS students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- Create submissions table
CREATE TABLE IF NOT EXISTS submissions (
    submission_id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(student_id),
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    fc DOUBLE PRECISION, -- Fluency and Coherence score
    lr DOUBLE PRECISION, -- Lexical Resource score
    gr DOUBLE PRECISION, -- Grammatical Range score
    pr DOUBLE PRECISION, -- Pronunciation score
    overall DOUBLE PRECISION, -- Overall score
    overall_comment TEXT  -- Contains feedback including teacher comments
);

-- Insert sample students
INSERT INTO students (student_id, name, email)
VALUES 
    (1, 'Bob Smith', 'anhnheiowru@gmail.com'),
    (2, 'Alice Johnson', 'aj153006@gmail.com'),
    (3, 'Charlie Brown', 'charlieb131@gmail.com'),
    (4, 'David White', 'davidwwh898@gmail.com'),
    (5, 'Emma Green', 'emmaG746@gmail.com'),
    (9, 'Alice Johnson', 'alice.johnson@example.com')
ON CONFLICT (student_id) DO NOTHING;

-- Insert sample submissions
INSERT INTO submissions (student_id, submitted_at, fc, lr, gr, pr, overall, overall_comment)
VALUES
    (1, '2023-02-19 22:04:00', 7, 7.5, 8, 7.5, 7.5, 'Very good! You have strong language skills.'),
    (1, '2023-02-20 18:30:00', 7.5, 8, 7.5, 7.5, 8, 'Excellent! You speak well.'),
    (2, '2023-02-19 21:15:00', 6, 5, 7, 6, 6, 'Fair! You can communicate but need improvement.'),
    (2, '2023-02-21 14:45:00', 7, 6.5, 7, 6, 6.5, 'Fair! You can communicate clearly.'),
    (3, '2023-02-19 23:30:00', 8.5, 8, 7.5, 8, 8, 'Excellent! You speak well.'),
    (3, '2023-02-22 07:20:00', 9, 9, 9, 9, 9, 'Outstanding! Your fluency is excellent.')
ON CONFLICT DO NOTHING; 