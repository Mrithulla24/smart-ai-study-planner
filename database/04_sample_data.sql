USE smart_ai_study_planner;
INSERT INTO students(name,email,course,year,goal) VALUES
('Arun Kumar','arun@example.com','B.Tech IT',2,'Improve programming skills'),
('Priya Sharma','priya@example.com','B.Tech CSE',2,'Improve academic performance'),
('Rahul Raj','rahul@example.com','B.Sc Computer Science',1,'Build strong programming fundamentals'),
('Ananya Devi','ananya@example.com','B.Tech IT',3,'Prepare for placement interviews');
INSERT INTO subjects(subject_name,topic,priority) VALUES
('Python Programming','Functions and OOP','HIGH'),('Database Management','SQL and Normalization','HIGH'),('Data Structures','Arrays and Linked Lists','HIGH'),('Computer Networks','Networking Fundamentals','MEDIUM'),('Operating Systems','Process Management','MEDIUM'),('Mathematics','Probability and Statistics','LOW');
INSERT INTO performance(student_id,subject_id,score,attendance,study_hours,previous_score) VALUES
(1,1,55,78,2,60),(1,2,72,88,3,68),(1,3,48,70,1,55),
(2,1,82,92,4,78),(2,2,65,80,2,70),(2,4,74,86,3,72),
(3,3,52,72,1.5,58),(3,5,68,76,2,65),(3,6,79,90,3,75),
(4,1,88,95,4,84),(4,3,76,89,3,72),(4,4,61,78,2,66);
