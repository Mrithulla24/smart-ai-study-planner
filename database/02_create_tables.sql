USE smart_ai_study_planner;
CREATE TABLE IF NOT EXISTS students (
 student_id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 email VARCHAR(150) NOT NULL,
 course VARCHAR(100) NOT NULL,
 year INT NOT NULL,
 goal VARCHAR(255) NULL
);
CREATE TABLE IF NOT EXISTS subjects (
 subject_id INT AUTO_INCREMENT PRIMARY KEY,
 subject_name VARCHAR(100) NOT NULL,
 topic VARCHAR(150) NOT NULL,
 priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM'
);
CREATE TABLE IF NOT EXISTS performance (
 performance_id INT AUTO_INCREMENT PRIMARY KEY,
 student_id INT NOT NULL,
 subject_id INT NOT NULL,
 score DECIMAL(5,2) NOT NULL,
 attendance DECIMAL(5,2) NOT NULL,
 study_hours DECIMAL(5,2) NOT NULL,
 previous_score DECIMAL(5,2) NOT NULL,
 CONSTRAINT fk_performance_student FOREIGN KEY(student_id) REFERENCES students(student_id),
 CONSTRAINT fk_performance_subject FOREIGN KEY(subject_id) REFERENCES subjects(subject_id)
);
CREATE TABLE IF NOT EXISTS study_plans (
 plan_id INT AUTO_INCREMENT PRIMARY KEY,
 student_id INT NOT NULL,
 subject_id INT NOT NULL,
 plan_date DATE NOT NULL,
 recommended_hours DECIMAL(5,2) NOT NULL,
 priority VARCHAR(20) NOT NULL,
 recommendation TEXT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
 CONSTRAINT fk_study_plan_student FOREIGN KEY(student_id) REFERENCES students(student_id),
 CONSTRAINT fk_study_plan_subject FOREIGN KEY(subject_id) REFERENCES subjects(subject_id)
);
CREATE TABLE IF NOT EXISTS study_progress (
 progress_id INT AUTO_INCREMENT PRIMARY KEY,
 student_id INT NOT NULL,
 plan_id INT NOT NULL,
 hours_completed DECIMAL(5,2) NOT NULL DEFAULT 0,
 completion_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
 progress_date DATE NOT NULL,
 CONSTRAINT fk_progress_student FOREIGN KEY(student_id) REFERENCES students(student_id),
 CONSTRAINT fk_progress_plan FOREIGN KEY(plan_id) REFERENCES study_plans(plan_id)
);
