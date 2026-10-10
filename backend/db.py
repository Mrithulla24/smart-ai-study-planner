import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'YOUR_MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE', 'smart_ai_study_planner')
    )


def ensure_extra_tables():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_sessions (
            session_id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            plan_id INT NULL,
            subject_id INT NULL,
            duration_minutes DECIMAL(8,2) NOT NULL DEFAULT 0,
            session_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
            notes TEXT NULL,
            CONSTRAINT fk_session_student FOREIGN KEY (student_id) REFERENCES students(student_id),
            CONSTRAINT fk_session_plan FOREIGN KEY (plan_id) REFERENCES study_plans(plan_id),
            CONSTRAINT fk_session_subject FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_settings (
            notification_id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL UNIQUE,
            email_enabled TINYINT(1) NOT NULL DEFAULT 0,
            sms_enabled TINYINT(1) NOT NULL DEFAULT 0,
            email VARCHAR(150) NULL,
            mobile VARCHAR(30) NULL,
            reminder_minutes INT NOT NULL DEFAULT 30,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_notification_student FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')
    connection.commit()
    cursor.close()
    connection.close()
