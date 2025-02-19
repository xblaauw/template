-- Insert sample users
INSERT INTO users (email, password_hash, verification_key, is_verified) VALUES
('admin@example.com', '$2b$12$PyTLhFBdMcq0Scmts2Z9FOQ135XMpiviVGeKKVtADORAwJSQTdQG6', uuid_generate_v4(), true),
('teacher1@example.com', '$2b$12$PyTLhFBdMcq0Scmts2Z9FOQ135XMpiviVGeKKVtADORAwJSQTdQG6', uuid_generate_v4(), true),
('teacher2@example.com', '$2b$12$PyTLhFBdMcq0Scmts2Z9FOQ135XMpiviVGeKKVtADORAwJSQTdQG6', uuid_generate_v4(), true),
('student1@example.com', '$2b$12$PyTLhFBdMcq0Scmts2Z9FOQ135XMpiviVGeKKVtADORAwJSQTdQG6', uuid_generate_v4(), true),
('student2@example.com', '$2b$12$PyTLhFBdMcq0Scmts2Z9FOQ135XMpiviVGeKKVtADORAwJSQTdQG6', uuid_generate_v4(), false);

-- Insert credits for users
INSERT INTO credits (user_id, amount, stripe_payment_id) VALUES
(1, 100, 'stripe_payment_1'),
(2, 50, 'stripe_payment_2'),
(3, 75, 'stripe_payment_3');

-- Insert classes
INSERT INTO classes (owner_id, name) VALUES
(1, 'Advanced Mathematics'),
(2, 'Basic Science'),
(3, 'Computer Programming');

-- Insert students into classes
INSERT INTO students (class_id, user_id) VALUES
(1, 4),
(1, 5),
(2, 4);

-- Insert media
INSERT INTO media (alt_text, path) VALUES
('Introduction Diagram', 'data/intro-diagram.png'),
('Course Overview', 'data/course-overview.jpg'),
('Module 1 Banner', 'data/module1-banner.png');

-- Insert courses
INSERT INTO courses (name, version, description, credit_cost) VALUES
('Mathematics 101', 1, 'Basic mathematics course', 2),
('Science Fundamentals', 1, 'Introduction to science', 1),
('Programming Basics', 1, 'Learn programming fundamentals', 3);

-- Link courses with media
INSERT INTO course_media (course_id, media_id) VALUES
(1, 1),
(2, 2),
(3, 3);

-- Insert enrollments
INSERT INTO enrollments (class_id, course_id) VALUES
(1, 1),
(2, 2),
(3, 3);

-- Insert modules
INSERT INTO modules (course_id, name, version, description, sequence_number) VALUES
(1, 'Introduction to Algebra', 1, 'Basic algebra concepts', 1),
(1, 'Linear Equations', 1, 'Understanding linear equations', 2),
(2, 'Scientific Method', 1, 'Learning the scientific method', 1);

-- Insert module pages
INSERT INTO module_pages (module_id, name, version, description, sequence_number) VALUES
(1, 'Algebra Basics', 1, 'Introduction to basic algebra', 1),
(1, 'Variables and Constants', 1, 'Understanding variables', 2),
(2, 'Solving Equations', 1, 'Methods for solving equations', 1);

-- Insert multiple choice questions
INSERT INTO questions_mc (module_page_id, context, question) VALUES
(1, 'Basic algebra practice', 'What is the value of x in 2x + 4 = 10?'),
(1, 'Variable identification', 'Which of the following is a variable?'),
(2, 'Equation solving', 'How do you isolate a variable?');

-- Insert answer options
INSERT INTO answer_options (question_mc_id, option_text, feedback_message) VALUES
(1, '3', 'Correct! 2(3) + 4 = 10'),
(1, '4', 'Try again. 2(4) + 4 = 12'),
(1, '2', 'Try again. 2(2) + 4 = 8'),
(2, 'x', 'Correct! x is a variable'),
(2, '5', 'Numbers are constants, not variables');

-- Insert correct answers
INSERT INTO answer_option_correctness (question_mc_id, answer_option_id) VALUES
(1, 1),
(2, 4);

-- Insert assignments
INSERT INTO assignments (student_id, question_mc_id, test_date, access_token, status) VALUES
(1, 1, CURRENT_DATE, uuid_generate_v4(), 'pending'),
(1, 2, CURRENT_DATE, uuid_generate_v4(), 'sent'),
(2, 1, CURRENT_DATE, uuid_generate_v4(), 'completed');

-- Insert certificates
INSERT INTO certificates (student_id, course_id, access_token, valid_until) VALUES
(1, 1, uuid_generate_v4(), CURRENT_DATE + INTERVAL '1 year'),
(2, 2, uuid_generate_v4(), CURRENT_DATE + INTERVAL '1 year');

-- Insert assignment visits
INSERT INTO assignment_visits (assignment_id) VALUES
(1),
(2),
(3);

-- Insert assignment attempts
INSERT INTO assignment_attempts (assignment_visit_id, answer_option_id) VALUES
(1, 1),
(2, 4),
(3, 1);