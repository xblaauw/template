CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT * FROM pg_extension WHERE extname = 'pg_cron';



--------- TABLES



-- Stores registered users and their verification status
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    verification_key UUID UNIQUE,  -- used for automatic user verification using query-params in the url
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- tracks user-purchased course-credits that can be used to enroll user-classe-students into a course
CREATE TABLE credits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount INT NOT NULL,
    stripe_payment_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Core tables
CREATE TABLE classes (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Users can create and administer classes
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, class_id)
);

-- stores media paths from data/uuid.ext folder on the platform
CREATE TABLE media (
    id SERIAL PRIMARY KEY,
    alt_text TEXT NOT NULL,
    path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- stores course metadata
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version INT NOT NULL,
    description TEXT,  -- markdown contains links to media like [alt_text](path)
    certificate_valid_duration INTERVAL NOT NULL DEFAULT INTERVAL '1 year',
    credit_cost INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, version)
);

-- stores course media links
CREATE TABLE course_media (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- tracks which users are enrolled in which course
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- stores module metadata
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    version INT NOT NULL DEFAULT 1,
    description TEXT,  -- markdown contains links to media like [alt_text](path)
    sequence_number INT NOT NULL,
    UNIQUE (name, version),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- stores module media links
CREATE TABLE module_media (
    id SERIAL PRIMARY KEY,
    module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE,
    media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- stores module page content as markdown
CREATE TABLE module_pages (
    id SERIAL PRIMARY KEY,
    module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    version INT NOT NULL,
    description TEXT,  -- markdown contains links to media like [alt_text](path)
    sequence_number INT NOT NULL,
    UNIQUE (name, version),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- stores module media links
CREATE TABLE module_page_media (
    id SERIAL PRIMARY KEY,
    module_page_id INTEGER REFERENCES module_pages(id) ON DELETE CASCADE,
    media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- contains all multiple-choice questions
CREATE TABLE questions_mc (
    id SERIAL PRIMARY KEY,
    module_page_id INTEGER REFERENCES module_pages(id) ON DELETE CASCADE,
    context TEXT,  -- markdown contains links to media like [alt_text](path)
    question TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- stores module media links
CREATE TABLE questions_mc_media (
    id SERIAL PRIMARY KEY,
    questions_mc_id INTEGER REFERENCES questions_mc(id) ON DELETE CASCADE,
    media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- lists available answer options
CREATE TABLE answer_options (
    id SERIAL PRIMARY KEY,
    question_mc_id INTEGER REFERENCES questions_mc(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    feedback_message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- stores which answer is correct
CREATE TABLE answer_option_correctness (
    id SERIAL PRIMARY KEY,
    question_mc_id INTEGER REFERENCES questions_mc(id) ON DELETE CASCADE,
    answer_option_id INTEGER REFERENCES answer_options(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_mc_id, answer_option_id),
    UNIQUE(question_mc_id)
);

-- assigns a question to a user
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    question_mc_id INTEGER REFERENCES questions_mc(id) ON DELETE CASCADE,
    test_date DATE NOT NULL,
    access_token UUID UNIQUE NOT NULL,  -- used for automatic assignment tracking using query-params in the url
    expiration_date DATE NOT NULL DEFAULT CURRENT_DATE + INTERVAL '1 year',
    status VARCHAR(20) CHECK (status IN ('pending', 'sent', 'completed', 'expired')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- logs whenever a user visits the assignment page
CREATE TABLE assignment_visits (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER REFERENCES assignments(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- logs whenever the user commits to a specific answer option
CREATE TABLE assignment_attempts (
    id SERIAL PRIMARY KEY,
    assignment_visit_id INTEGER REFERENCES assignment_visits(id) ON DELETE CASCADE,
    answer_option_id INTEGER REFERENCES answer_options(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- logs course-completion and allows for certificate checking even when other data is deleted from the db
CREATE TABLE certificates (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    course_id INTEGER REFERENCES courses(id),
    access_token UUID UNIQUE NOT NULL, -- used for automatic certificate verification using query-params in the url (api will check, does the uuid exist in this table, and is the created_at date less then a year old)
    valid_until DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);



--------- INDEXES



-- User Authentication & Verification
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_verification_key ON users(verification_key);

-- classe Management
CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_students_org_id ON students(class_id);
CREATE INDEX idx_students_composite ON students(user_id, class_id);

-- Course & Module Navigation
CREATE INDEX idx_modules_course_id ON modules(course_id);
CREATE INDEX idx_module_pages_module_id ON module_pages(module_id);
CREATE INDEX idx_questions_mc_module_page_id ON questions_mc(module_page_id);

-- Assignment Management
CREATE INDEX idx_assignments_student_id ON assignments(student_id);
CREATE INDEX idx_assignments_access_token ON assignments(access_token);
CREATE INDEX idx_assignments_status ON assignments(status);
CREATE INDEX idx_assignments_test_date ON assignments(test_date);
CREATE INDEX idx_assignments_composite ON assignments(student_id, status, test_date);

-- Progress Tracking
CREATE INDEX idx_assignment_visits_assignment_id ON assignment_visits(assignment_id);
CREATE INDEX idx_assignment_attempts_visit_id ON assignment_attempts(assignment_visit_id);
CREATE INDEX idx_enrollments_composite ON enrollments(class_id, course_id);

-- Certificate Management
CREATE INDEX idx_certificates_access_token ON certificates(access_token);
CREATE INDEX idx_certificates_validity ON certificates(student_id, course_id, valid_until);

-- Credits System
CREATE INDEX idx_credits_user_id ON credits(user_id);

-- Page Navigation & Content Structure
CREATE INDEX idx_module_pages_sequence ON module_pages(module_id, sequence_number);
CREATE INDEX idx_modules_sequence ON modules(course_id, sequence_number);

-- Question classe
CREATE INDEX idx_questions_mc_page_composite ON questions_mc(module_page_id, id);



-------- VIEWS



CREATE OR REPLACE VIEW user_available_credits AS
SELECT 
    u.id AS user_id,
    u.email,
    COALESCE(SUM(c.amount), 0) AS available_credits,
    COUNT(c.id) AS total_transactions,
    MAX(c.created_at) AS last_transaction_date
FROM users u
LEFT JOIN credits c ON u.id = c.user_id
GROUP BY u.id, u.email;



------- FUNCTIONS



-- Update assignment status to 'completed' only when the correct answer is given
CREATE OR REPLACE FUNCTION update_assignment_completion()
RETURNS TRIGGER AS $$
BEGIN
    -- If answer is correct
    IF EXISTS (
        SELECT 1 
        FROM answer_option_correctness 
        WHERE answer_option_id = NEW.answer_option_id
    ) THEN
        -- Mark assignment completed
        UPDATE assignments 
        SET status = 'completed'
        WHERE id = (
            SELECT assignment_id 
            FROM assignment_visits 
            WHERE id = NEW.assignment_visit_id
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_assignment_attempt
AFTER INSERT ON assignment_attempts
FOR EACH ROW
EXECUTE FUNCTION update_assignment_completion();



-------- CRON FUNCTIONS



-- Function to update expired assignments
CREATE OR REPLACE FUNCTION update_expired_assignments()
RETURNS void AS $$
BEGIN
    UPDATE assignments 
    SET status = 'expired'
    WHERE expiration_date < CURRENT_DATE 
    AND status != 'expired'
    AND status != 'completed';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION daily_maintenance()
RETURNS void AS $$
BEGIN
    
    -- Update expired assignments
    PERFORM update_expired_assignments();

END;
$$ LANGUAGE plpgsql;

-- Schedule daily maintenance
SELECT cron.schedule('0 0 * * *', $$SELECT daily_maintenance()$$);



