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

-- tracks user-purchased course-credits that can be used to enroll user-organization-students into a course
CREATE TABLE credits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    mutation VARCHAR(10) CHECK (mutation IN ('add', 'remove')),
    amount INT NOT NULL,
    stripe_payment_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Core tables
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    domain VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Users can create and administer organizations
CREATE TABLE users_organizations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(10) CHECK (role IN ('student', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, organization_id, role)
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
    version INT NOT NULL UNIQUE,
    description TEXT,  -- markdown contains links to media like [alt_text](path)
    certificate_valid_duration INTERVAL NOT NULL DEFAULT INTERVAL '1 year',
    credit_cost INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
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
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- stores module metadata
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    version INT NOT NULL UNIQUE,
    description TEXT,  -- markdown contains links to media like [alt_text](path)
    sequence_number INT NOT NULL,
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
    version INT NOT NULL UNIQUE,
    description TEXT,  -- markdown contains links to media like [alt_text](path)
    sequence_number INT NOT NULL,
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
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
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
    user_id INTEGER REFERENCES users(id),
    course_id INTEGER REFERENCES courses(id),
    access_token UUID UNIQUE NOT NULL, -- used for automatic certificate verification using query-params in the url (api will check, does the uuid exist in this table, and is the created_at date less then a year old)
    valid_until DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);



--------- INDEXES



-- User Authentication & Verification
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_verification_key ON users(verification_key);

-- Organization Management
CREATE INDEX idx_users_organizations_user_id ON users_organizations(user_id);
CREATE INDEX idx_users_organizations_org_id ON users_organizations(organization_id);
CREATE INDEX idx_users_organizations_composite ON users_organizations(user_id, organization_id, role);

-- Course & Module Navigation
CREATE INDEX idx_modules_course_id ON modules(course_id);
CREATE INDEX idx_module_pages_module_id ON module_pages(module_id);
CREATE INDEX idx_questions_mc_module_page_id ON questions_mc(module_page_id);

-- Assignment Management
CREATE INDEX idx_assignments_user_id ON assignments(user_id);
CREATE INDEX idx_assignments_access_token ON assignments(access_token);
CREATE INDEX idx_assignments_status ON assignments(status);
CREATE INDEX idx_assignments_test_date ON assignments(test_date);
CREATE INDEX idx_assignments_composite ON assignments(user_id, status, test_date);

-- Progress Tracking
CREATE INDEX idx_assignment_visits_assignment_id ON assignment_visits(assignment_id);
CREATE INDEX idx_assignment_attempts_visit_id ON assignment_attempts(assignment_visit_id);
CREATE INDEX idx_enrollments_composite ON enrollments(user_id, course_id);

-- Certificate Management
CREATE INDEX idx_certificates_access_token ON certificates(access_token);
CREATE INDEX idx_certificates_validity ON certificates(user_id, course_id, valid_until);

-- Credits System
CREATE INDEX idx_credits_user_id ON credits(user_id);
CREATE INDEX idx_credits_composite ON credits(user_id, mutation);

-- Page Navigation & Content Structure
CREATE INDEX idx_module_pages_sequence ON module_pages(module_id, sequence_number);
CREATE INDEX idx_modules_sequence ON modules(course_id, sequence_number);

-- Question Organization
CREATE INDEX idx_questions_mc_page_composite ON questions_mc(module_page_id, id);



-------- VIEWS



-- View to calculate module completion status
CREATE VIEW module_completion_status AS
WITH module_questions AS (
    SELECT m.id as module_id, 
           m.course_id,
           COUNT(DISTINCT qmc.id) as total_questions
    FROM modules m
    JOIN module_pages mp ON mp.module_id = m.id
    JOIN questions_mc qmc ON qmc.module_page_id = mp.id
    GROUP BY m.id, m.course_id
),
user_completed_questions AS (
    SELECT m.id as module_id,
           a.user_id,
           COUNT(DISTINCT aa.assignment_visit_id) as completed_questions
    FROM modules m
    JOIN module_pages mp ON mp.module_id = m.id
    JOIN questions_mc qmc ON qmc.module_page_id = mp.id
    JOIN assignments a ON a.question_mc_id = qmc.id
    JOIN assignment_visits av ON av.assignment_id = a.id
    JOIN assignment_attempts aa ON aa.assignment_visit_id = av.id
    GROUP BY m.id, a.user_id
)
SELECT 
    mq.module_id,
    mq.course_id,
    ucq.user_id,
    mq.total_questions,
    COALESCE(ucq.completed_questions, 0) as completed_questions,
    CASE 
        WHEN ucq.completed_questions IS NULL THEN 'not_started'
        WHEN ucq.completed_questions < mq.total_questions THEN 'in_progress'
        ELSE 'completed'
    END as status
FROM module_questions mq
LEFT JOIN user_completed_questions ucq ON ucq.module_id = mq.module_id;


-- View for course completion status
CREATE VIEW course_completion_status AS
SELECT 
    course_id,
    user_id,
    COUNT(DISTINCT module_id) as total_modules,
    COUNT(DISTINCT CASE WHEN status = 'completed' THEN module_id END) as completed_modules,
    CASE 
        WHEN COUNT(DISTINCT CASE WHEN status != 'not_started' THEN module_id END) = 0 THEN 'not_started'
        WHEN COUNT(DISTINCT CASE WHEN status = 'completed' THEN module_id END) = COUNT(DISTINCT module_id) THEN 'completed'
        ELSE 'in_progress'
    END as status
FROM module_completion_status
GROUP BY course_id, user_id;


-- Organization Overview (shows admins and their student counts)
CREATE VIEW organization_overview AS
SELECT 
    o.id as org_id,
    o.name as org_name,
    o.domain,
    admin.email as admin_email,
    COUNT(DISTINCT student.id) as student_count
FROM organizations o
JOIN users_organizations uo_admin ON o.id = uo_admin.organization_id AND uo_admin.role = 'admin'
JOIN users admin ON uo_admin.user_id = admin.id
LEFT JOIN users_organizations uo_student ON o.id = uo_student.organization_id AND uo_student.role = 'student'
LEFT JOIN users student ON uo_student.user_id = student.id
GROUP BY o.id, o.name, o.domain, admin.email;


-- Organization Credit Balance (per organization admin)
CREATE VIEW organization_credit_balance AS
SELECT 
    o.id as org_id,
    o.name as org_name,
    admin.email as admin_email,
    COALESCE(SUM(CASE 
        WHEN c.mutation = 'add' THEN c.amount 
        WHEN c.mutation = 'remove' THEN -c.amount 
    END), 0) as available_credits,
    COUNT(DISTINCT e.id) as active_enrollments
FROM organizations o
JOIN users_organizations uo ON o.id = uo.organization_id AND uo.role = 'admin'
JOIN users admin ON uo.user_id = admin.id
LEFT JOIN credits c ON admin.id = c.user_id
LEFT JOIN users_organizations uo_students ON o.id = uo_students.organization_id AND uo_students.role = 'student'
LEFT JOIN enrollments e ON uo_students.user_id = e.user_id
GROUP BY o.id, o.name, admin.email;


-- Organization Student Progress (overview of student progress per organization)
CREATE VIEW organization_student_progress AS
SELECT 
    o.id as org_id,
    o.name as org_name,
    student.email as student_email,
    c.id as course_id,
    c.name as course_name,
    ccs.status as course_status,
    COUNT(DISTINCT a.id) as total_assignments,
    COUNT(DISTINCT CASE WHEN a.status = 'completed' THEN a.id END) as completed_assignments
FROM organizations o
JOIN users_organizations uo ON o.id = uo.organization_id AND uo.role = 'student'
JOIN users student ON uo.user_id = student.id
JOIN enrollments e ON student.id = e.user_id
JOIN courses c ON e.course_id = c.id
LEFT JOIN course_completion_status ccs ON c.id = ccs.course_id AND student.id = ccs.user_id
LEFT JOIN assignments a ON student.id = a.user_id
GROUP BY o.id, o.name, student.email, c.id, c.name, ccs.status;


-- Student Assignment Status
CREATE VIEW student_assignment_status AS
SELECT 
    u.id as user_id,
    u.email,
    c.id as course_id,
    c.name as course_name,
    m.id as module_id,
    m.name as module_name,
    a.id as assignment_id,
    a.test_date,
    a.status,
    CASE 
        WHEN aa.id IS NOT NULL THEN true 
        ELSE false 
    END as has_attempted,
    ao.option_text as last_answer,
    aoc.answer_option_id IS NOT NULL as was_correct
FROM users u
JOIN assignments a ON u.id = a.user_id
JOIN questions_mc qmc ON a.question_mc_id = qmc.id
JOIN module_pages mp ON qmc.module_page_id = mp.id
JOIN modules m ON mp.module_id = m.id
JOIN courses c ON m.course_id = c.id
LEFT JOIN assignment_visits av ON a.id = av.assignment_id
LEFT JOIN assignment_attempts aa ON av.id = aa.assignment_visit_id
LEFT JOIN answer_options ao ON aa.answer_option_id = ao.id
LEFT JOIN answer_option_correctness aoc ON ao.id = aoc.answer_option_id;


-- User Organization Overview
CREATE VIEW user_organization_overview AS
SELECT 
    u.id as user_id,
    u.email,
    o.id as org_id,
    o.name as org_name,
    uo.role,
    COUNT(DISTINCT e.course_id) as enrolled_courses
FROM users u
JOIN users_organizations uo ON u.id = uo.user_id
JOIN organizations o ON uo.organization_id = o.id
LEFT JOIN enrollments e ON u.id = e.user_id
GROUP BY u.id, u.email, o.id, o.name, uo.role;


-- Information to verify certificate authenticity
CREATE VIEW certificate_validation AS
SELECT 
    cert.access_token,
    u.email,
    o.name as organization_name,
    c.name as course_name,
    cert.created_at as completion_date,
    cert.valid_until
FROM certificates cert
JOIN users u ON cert.user_id = u.id
JOIN users_organizations uo ON u.id = uo.user_id
JOIN organizations o ON uo.organization_id = o.id
JOIN courses c ON cert.course_id = c.id
WHERE cert.valid_until >= CURRENT_DATE;


-- Check which assignments are currenty pending
CREATE VIEW pending_assignments AS
SELECT 
    a.id as assignment_id,
    u.email,
    a.test_date,
    a.access_token
FROM assignments a
JOIN users u ON a.user_id = u.id
WHERE a.status = 'pending' ;



------- FUNCTIONS



-- Function to check course completion and generate certificate if needed
CREATE OR REPLACE FUNCTION check_course_completion_and_generate_certificate(
    p_user_id INTEGER,
    p_course_id INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
    v_is_completed BOOLEAN;
BEGIN
    -- Check if course is completed
    SELECT EXISTS (
        SELECT 1 
        FROM course_completion_status 
        WHERE user_id = p_user_id 
        AND course_id = p_course_id 
        AND status = 'completed'
    ) INTO v_is_completed;

    -- If completed and no valid certificate exists, generate one
    IF v_is_completed THEN
        INSERT INTO certificates (
            user_id,
            course_id,
            access_token,
            valid_until
        )
        SELECT 
            p_user_id,
            p_course_id,
            gen_random_uuid(),
            CURRENT_DATE + (SELECT certificate_valid_duration FROM courses WHERE id = p_course_id)
        WHERE NOT EXISTS (
            SELECT 1 FROM certificates 
            WHERE user_id = p_user_id 
            AND course_id = p_course_id
            AND valid_until >= CURRENT_DATE
        );
    END IF;

    RETURN v_is_completed;
END;
$$ LANGUAGE plpgsql;


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



