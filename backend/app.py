from flask import Flask, jsonify, request
import re
from flask_cors import CORS
from db import get_connection, ensure_extra_tables
from notifications import send_email, send_sms
from recommendations import generate_recommendations, generate_study_plan

app = Flask(__name__)
CORS(app)

# The original backend API is preserved. CORS is enabled so the HTML frontend
# can call Flask when both are run locally on different ports.

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'success', 'message': 'Smart AI Study Planner backend is running'})

@app.route('/api/students', methods=['GET'])
def get_students():
    try:
        connection = get_connection(); cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT student_id, name, email, course, year, goal FROM students ORDER BY student_id')
        data = cursor.fetchall(); cursor.close(); connection.close()
        return jsonify({'status':'success','students':data})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}),500


@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json(silent=True) or {}
    required = ['name', 'email', 'course', 'year', 'goal']
    missing = [f for f in required if not str(data.get(f, '')).strip()]
    if missing:
        return jsonify({'status': 'error', 'message': f'Missing required field: {missing[0]}'}), 400

    name = str(data['name']).strip()
    email = str(data['email']).strip().lower()
    course = str(data['course']).strip()
    goal = str(data['goal']).strip()

    try:
        year = int(data['year'])
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Year must be a valid number'}), 400

    if len(name) < 2:
        return jsonify({'status': 'error', 'message': 'Name must contain at least 2 characters'}), 400
    if '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address'}), 400
    if year < 1 or year > 8:
        return jsonify({'status': 'error', 'message': 'Year must be between 1 and 8'}), 400

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute('SELECT student_id FROM students WHERE LOWER(email)=%s LIMIT 1', (email,))
        if cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'status': 'error', 'message': 'An account with this email already exists'}), 409

        cursor.execute(
            "INSERT INTO students (name, email, course, year, goal) VALUES (%s, %s, %s, %s, %s)",
            (name, email, course, year, goal)
        )
        connection.commit()
        student_id = cursor.lastrowid

        cursor.execute(
            'SELECT student_id, name, email, course, year, goal FROM students WHERE student_id=%s',
            (student_id,)
        )
        student = cursor.fetchone()

        cursor.close()
        connection.close()

        return jsonify({
            'status': 'success',
            'message': 'Student account created successfully',
            'student': student
        }), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    try:
        connection=get_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute('SELECT subject_id, subject_name, topic, priority FROM subjects ORDER BY subject_id')
        data=cursor.fetchall(); cursor.close(); connection.close()
        return jsonify({'status':'success','subjects':data})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/performance/<int:student_id>', methods=['GET'])
def get_performance(student_id):
    try:
        connection=get_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute('SELECT student_id,name FROM students WHERE student_id=%s',(student_id,)); student=cursor.fetchone()
        if not student:
            cursor.close(); connection.close(); return jsonify({'status':'error','message':'Student not found'}),404
        cursor.execute('''SELECT p.performance_id,p.student_id,p.subject_id,s.subject_name,s.topic,p.score,p.attendance,p.study_hours,p.previous_score FROM performance p JOIN subjects s ON p.subject_id=s.subject_id WHERE p.student_id=%s ORDER BY p.performance_id''',(student_id,))
        data=cursor.fetchall(); cursor.close(); connection.close()
        return jsonify({'status':'success','student_id':student_id,'student_name':student['name'],'performance':data})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/performance', methods=['POST'])
def add_performance():
    data=request.get_json(silent=True) or {}
    fields=['student_id','subject_id','score','attendance','study_hours','previous_score']
    missing=[f for f in fields if f not in data]
    if missing: return jsonify({'status':'error','message':'Missing required field: '+missing[0]}),400
    for f in ['score','attendance','previous_score']:
        if not isinstance(data[f],(int,float)) or not 0 <= data[f] <= 100: return jsonify({'status':'error','message':f'{f} must be a number between 0 and 100'}),400
    if not isinstance(data['study_hours'],(int,float)) or data['study_hours'] < 0: return jsonify({'status':'error','message':'study_hours must be a non-negative number'}),400
    try:
        connection=get_connection(); cursor=connection.cursor()
        cursor.execute('SELECT student_id FROM students WHERE student_id=%s',(data['student_id'],))
        if not cursor.fetchone(): cursor.close(); connection.close(); return jsonify({'status':'error','message':'Student not found'}),404
        cursor.execute('SELECT subject_id FROM subjects WHERE subject_id=%s',(data['subject_id'],))
        if not cursor.fetchone(): cursor.close(); connection.close(); return jsonify({'status':'error','message':'Subject not found'}),404
        cursor.execute('INSERT INTO performance (student_id,subject_id,score,attendance,study_hours,previous_score) VALUES (%s,%s,%s,%s,%s,%s)',tuple(data[f] for f in fields))
        connection.commit(); pid=cursor.lastrowid; cursor.close(); connection.close()
        return jsonify({'status':'success','message':'Performance added successfully','performance_id':pid}),201
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/recommendations/<int:student_id>', methods=['GET'])
def get_recommendations(student_id):
    try:
        connection=get_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute('SELECT student_id,name FROM students WHERE student_id=%s',(student_id,)); student=cursor.fetchone()
        if not student: cursor.close(); connection.close(); return jsonify({'status':'error','message':'Student not found'}),404
        cursor.execute('''SELECT p.subject_id,s.subject_name,s.topic,p.score,p.attendance,p.study_hours,p.previous_score FROM performance p JOIN subjects s ON p.subject_id=s.subject_id WHERE p.student_id=%s ORDER BY p.performance_id''',(student_id,))
        data=cursor.fetchall(); cursor.close(); connection.close()
        return jsonify({'status':'success','student_id':student_id,'student_name':student['name'],'recommendations':generate_recommendations(data)})
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/study-plan/<int:student_id>', methods=['GET'])
def get_study_plan(student_id):
    try:
        connection=get_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute('SELECT student_id,name FROM students WHERE student_id=%s',(student_id,)); student=cursor.fetchone()
        if not student: cursor.close(); connection.close(); return jsonify({'status':'error','message':'Student not found'}),404
        cursor.execute('''SELECT p.plan_id,p.student_id,p.subject_id,s.subject_name,s.topic,p.plan_date,p.recommended_hours,p.priority,p.recommendation,p.status FROM study_plans p JOIN subjects s ON p.subject_id=s.subject_id WHERE p.student_id=%s ORDER BY p.plan_date DESC,p.plan_id DESC''',(student_id,))
        data=cursor.fetchall(); cursor.close(); connection.close()
        return jsonify({'status':'success','student_id':student_id,'student_name':student['name'],'study_plan':data})
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/generate-study-plan/<int:student_id>', methods=['POST'])
def generate_student_study_plan(student_id):
    try:
        connection=get_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute('SELECT student_id,name FROM students WHERE student_id=%s',(student_id,)); student=cursor.fetchone()
        if not student: cursor.close(); connection.close(); return jsonify({'status':'error','message':'Student not found'}),404
        cursor.execute('''SELECT p.subject_id,s.subject_name,s.topic,p.score,p.attendance,p.study_hours,p.previous_score FROM performance p JOIN subjects s ON p.subject_id=s.subject_id WHERE p.student_id=%s ORDER BY p.performance_id''',(student_id,))
        perf=cursor.fetchall(); plans=generate_study_plan(generate_recommendations(perf)); created=[]; skipped=[]
        for plan in plans:
            cursor.execute("SELECT plan_id,status FROM study_plans WHERE student_id=%s AND subject_id=%s AND status IN ('PENDING','IN_PROGRESS') LIMIT 1",(student_id,plan['subject_id']))
            existing=cursor.fetchone()
            if existing:
                skipped.append({'subject_id':plan['subject_id'],'subject_name':plan['subject_name'],'existing_plan_id':existing['plan_id'],'existing_status':existing['status']}); continue
            cursor.execute('''INSERT INTO study_plans (student_id,subject_id,plan_date,recommended_hours,priority,recommendation,status) VALUES (%s,%s,CURDATE(),%s,%s,%s,%s)''',(student_id,plan['subject_id'],plan['recommended_hours'],plan['priority'],plan['recommendation'],plan['status']))
            created.append({**plan,'plan_id':cursor.lastrowid,'student_id':student_id})
        connection.commit(); cursor.close(); connection.close()
        return jsonify({'status':'success','message':'Personalized study plan generated successfully','student_id':student_id,'student_name':student['name'],'study_plan':created,'skipped_plans':skipped}),201
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/study-plan', methods=['POST'])
def add_study_plan():
    data=request.get_json(silent=True) or {}
    required=['student_id','subject_id','plan_date','recommended_hours','priority','recommendation','status']
    for f in required:
        if f not in data: return jsonify({'status':'error','message':f'Missing required field: {f}'}),400
    try:
        connection=get_connection(); cursor=connection.cursor()
        cursor.execute('INSERT INTO study_plans (student_id,subject_id,plan_date,recommended_hours,priority,recommendation,status) VALUES (%s,%s,%s,%s,%s,%s,%s)',tuple(data[f] for f in required))
        connection.commit(); pid=cursor.lastrowid; cursor.close(); connection.close()
        return jsonify({'status':'success','message':'Study plan added successfully','plan_id':pid}),201
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/progress/<int:student_id>', methods=['GET'])
def get_progress(student_id):
    try:
        connection=get_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute('SELECT student_id,name FROM students WHERE student_id=%s',(student_id,)); student=cursor.fetchone()
        if not student: cursor.close(); connection.close(); return jsonify({'status':'error','message':'Student not found'}),404
        cursor.execute('''SELECT sp.progress_id,sp.student_id,sp.plan_id,sp.hours_completed,sp.completion_status,sp.progress_date,s.subject_name,s.topic,p.recommended_hours,p.priority,p.status AS plan_status FROM study_progress sp JOIN study_plans p ON sp.plan_id=p.plan_id JOIN subjects s ON p.subject_id=s.subject_id WHERE sp.student_id=%s ORDER BY sp.progress_date DESC,sp.progress_id DESC''',(student_id,))
        data=cursor.fetchall(); cursor.close(); connection.close()
        return jsonify({'status':'success','student_id':student_id,'student_name':student['name'],'progress':data})
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/progress', methods=['POST'])
def add_progress():
    data=request.get_json(silent=True) or {}
    required=['student_id','plan_id','hours_completed','completion_status','progress_date']
    for f in required:
        if f not in data: return jsonify({'status':'error','message':f'Missing required field: {f}'}),400
    if data.get('completion_status') not in ('PARTIAL','COMPLETED'):
        return jsonify({'status':'error','message':'Progress status must be PARTIAL or COMPLETED'}),400
    try:
        connection=get_connection(); cursor=connection.cursor()
        cursor.execute('SELECT plan_id,status FROM study_plans WHERE plan_id=%s AND student_id=%s',(data['plan_id'],data['student_id']))
        plan=cursor.fetchone()
        if not plan: cursor.close(); connection.close(); return jsonify({'status':'error','message':'Study plan not found for this student'}),404
        if plan[1]=='COMPLETED': cursor.close(); connection.close(); return jsonify({'status':'error','message':'Cannot add progress to a completed study plan'}),400
        cursor.execute('INSERT INTO study_progress (student_id,plan_id,hours_completed,completion_status,progress_date) VALUES (%s,%s,%s,%s,%s)',tuple(data[f] for f in required))
        pid=cursor.lastrowid
        cursor.execute('UPDATE study_plans SET status=%s WHERE plan_id=%s AND student_id=%s',(data['completion_status'],data['plan_id'],data['student_id']))
        connection.commit(); cursor.close(); connection.close()
        return jsonify({'status':'success','message':'Progress added successfully','progress_id':pid}),201
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/profile/<int:student_id>', methods=['PUT'])
def update_profile(student_id):
    data = request.get_json(silent=True) or {}
    allowed = ['name', 'email', 'course', 'year', 'goal']
    fields = {key: data[key] for key in allowed if key in data}
    if not fields:
        return jsonify({'status': 'error', 'message': 'No profile fields supplied'}), 400

    # Normalize and validate values before touching the database.
    for key in ('name', 'email', 'course', 'goal'):
        if key in fields:
            fields[key] = str(fields[key] if fields[key] is not None else '').strip()
    if 'name' in fields and len(fields['name']) < 2:
        return jsonify({'status': 'error', 'message': 'Name must contain at least 2 characters'}), 400
    if 'course' in fields and not fields['course']:
        return jsonify({'status': 'error', 'message': 'Course cannot be empty'}), 400
    if 'email' in fields:
        fields['email'] = fields['email'].lower()
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', fields['email']):
            return jsonify({'status': 'error', 'message': 'Please enter a valid email address'}), 400
    if 'year' in fields:
        try:
            fields['year'] = int(fields['year'])
        except (TypeError, ValueError):
            return jsonify({'status': 'error', 'message': 'Year must be a valid number'}), 400
        if not 1 <= fields['year'] <= 8:
            return jsonify({'status': 'error', 'message': 'Year must be between 1 and 8'}), 400

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT student_id FROM students WHERE student_id=%s', (student_id,))
        if not cursor.fetchone():
            return jsonify({'status': 'error', 'message': 'Student not found. Please sign in again.'}), 404

        if 'email' in fields:
            cursor.execute('SELECT student_id FROM students WHERE LOWER(email)=%s AND student_id<>%s LIMIT 1', (fields['email'], student_id))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'Another student is already using this email'}), 409

        if fields:
            sets = ', '.join(f'{key}=%s' for key in fields)
            cursor.execute(f'UPDATE students SET {sets} WHERE student_id=%s', tuple(fields.values()) + (student_id,))
            connection.commit()

        # Fetching the row confirms success even when values were unchanged (rowcount == 0).
        cursor.execute('SELECT student_id, name, email, course, year, goal FROM students WHERE student_id=%s', (student_id,))
        updated_student = cursor.fetchone()
        return jsonify({'status': 'success', 'message': 'Profile updated successfully', 'student': updated_student})
    except Exception as exc:
        if connection:
            try: connection.rollback()
            except Exception: pass
        app.logger.exception('Profile update failed for student_id=%s', student_id)
        return jsonify({'status': 'error', 'message': 'Profile could not be saved. Verify the database connection and try again.'}), 500
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if connection:
            try: connection.close()
            except Exception: pass

@app.route('/api/study-sessions/<int:student_id>', methods=['GET'])
def get_study_sessions(student_id):
    try:
        connection=get_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute('SELECT ss.session_id,ss.student_id,ss.plan_id,ss.subject_id,sub.subject_name,sub.topic,ss.duration_minutes,ss.session_date,ss.status,ss.notes FROM study_sessions ss LEFT JOIN subjects sub ON ss.subject_id=sub.subject_id WHERE ss.student_id=%s ORDER BY ss.session_date DESC,ss.session_id DESC',(student_id,))
        data=cursor.fetchall(); cursor.close(); connection.close(); return jsonify({'status':'success','sessions':data})
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/study-sessions', methods=['POST'])
def add_study_session():
    data=request.get_json(silent=True) or {}
    for f in ['student_id','duration_minutes']:
        if f not in data: return jsonify({'status':'error','message':f'Missing required field: {f}'}),400
    try: duration=float(data['duration_minutes'])
    except (TypeError,ValueError): return jsonify({'status':'error','message':'duration_minutes must be a number'}),400
    if duration<=0: return jsonify({'status':'error','message':'Study duration must be greater than zero'}),400
    try:
        connection=get_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute('SELECT student_id FROM students WHERE student_id=%s',(data['student_id'],))
        if not cursor.fetchone(): cursor.close(); connection.close(); return jsonify({'status':'error','message':'Student not found'}),404
        plan_id=data.get('plan_id'); subject_id=data.get('subject_id')
        if plan_id:
            cursor.execute('SELECT subject_id FROM study_plans WHERE plan_id=%s AND student_id=%s',(plan_id,data['student_id'])); plan=cursor.fetchone()
            if not plan: cursor.close(); connection.close(); return jsonify({'status':'error','message':'Study plan not found'}),404
            subject_id=subject_id or plan['subject_id']
        cursor.execute('INSERT INTO study_sessions (student_id,plan_id,subject_id,duration_minutes,status,notes) VALUES (%s,%s,%s,%s,%s,%s)',(data['student_id'],plan_id,subject_id,duration,data.get('status','COMPLETED'),data.get('notes')))
        connection.commit(); sid=cursor.lastrowid
        cursor.execute('SELECT name,email FROM students WHERE student_id=%s',(data['student_id'],)); student=cursor.fetchone()
        cursor.close(); connection.close()
        # Notification is best-effort: a missing SMTP/Twilio configuration must not
        # prevent the study session from being saved.
        notification_errors=[]
        try:
            nconn=get_connection(); ncur=nconn.cursor(dictionary=True)
            ncur.execute('SELECT * FROM notification_settings WHERE student_id=%s',(data['student_id'],)); ns=ncur.fetchone(); ncur.close(); nconn.close()
            if ns:
                mins=round(duration,1); body=f"Hi {student['name']}, you completed a {mins}-minute SmartStudy session. Great work! Check your Progress page to see your updated study analytics."
                if ns.get('email_enabled') and ns.get('email'):
                    try: send_email(ns['email'],'SmartStudy study session completed',body)
                    except Exception as ex: notification_errors.append('Email: '+str(ex))
                if ns.get('sms_enabled') and ns.get('mobile'):
                    try: send_sms(ns['mobile'],body)
                    except Exception as ex: notification_errors.append('SMS: '+str(ex))
        except Exception as ex:
            notification_errors.append(str(ex))
        result={'status':'success','message':'Study session saved successfully','session_id':sid}
        if notification_errors: result['notification_errors']=notification_errors
        return jsonify(result),201
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/notifications/<int:student_id>', methods=['GET'])
def get_notification_settings(student_id):
    try:
        connection=get_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute('SELECT student_id,email_enabled,sms_enabled,email,mobile,reminder_minutes FROM notification_settings WHERE student_id=%s',(student_id,)); data=cursor.fetchone()
        if not data:
            cursor.execute('SELECT email FROM students WHERE student_id=%s',(student_id,)); st=cursor.fetchone(); data={'student_id':student_id,'email_enabled':0,'sms_enabled':0,'email':st['email'] if st else '','mobile':'','reminder_minutes':30}
        cursor.close(); connection.close(); return jsonify({'status':'success','settings':data})
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/notifications', methods=['POST'])
def save_notification_settings():
    data=request.get_json(silent=True) or {}
    if 'student_id' not in data: return jsonify({'status':'error','message':'Missing student_id'}),400
    try:
        connection=get_connection(); cursor=connection.cursor()
        cursor.execute("INSERT INTO notification_settings (student_id,email_enabled,sms_enabled,email,mobile,reminder_minutes) VALUES (%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE email_enabled=VALUES(email_enabled),sms_enabled=VALUES(sms_enabled),email=VALUES(email),mobile=VALUES(mobile),reminder_minutes=VALUES(reminder_minutes)",(data['student_id'],int(bool(data.get('email_enabled'))),int(bool(data.get('sms_enabled'))),data.get('email'),data.get('mobile'),int(data.get('reminder_minutes',30))))
        connection.commit(); cursor.close(); connection.close(); return jsonify({'status':'success','message':'Notification settings saved successfully'})
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

@app.route('/api/notifications/test/<int:student_id>', methods=['POST'])
def test_notification(student_id):
    try:
        connection=get_connection(); cursor=connection.cursor(dictionary=True)
        cursor.execute('SELECT ns.*,s.name FROM notification_settings ns JOIN students s ON ns.student_id=s.student_id WHERE ns.student_id=%s',(student_id,)); settings=cursor.fetchone(); cursor.close(); connection.close()
        if not settings: return jsonify({'status':'error','message':'Save notification settings first'}),400
        sent=[]; errors=[]; body=f"Hello {settings['name']}, this is a test notification from SmartStudy. Your personalized study planner is ready."
        if settings['email_enabled']:
            try: send_email(settings['email'],'SmartStudy test notification',body); sent.append('email')
            except Exception as e: errors.append(str(e))
        if settings['sms_enabled']:
            try: send_sms(settings['mobile'],body); sent.append('SMS')
            except Exception as e: errors.append(str(e))
        if not sent and errors: return jsonify({'status':'error','message':' | '.join(errors)}),400
        return jsonify({'status':'success','message':'Test notification sent via '+(', '.join(sent) if sent else 'no enabled channels'),'errors':errors})
    except Exception as e: return jsonify({'status':'error','message':str(e)}),500

if __name__ == '__main__':
    ensure_extra_tables()
    app.run(debug=True)
