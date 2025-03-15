from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
#from flask_mail import Mail, Message 
from datetime import timedelta
from flask_session import Session
import sqlite3
from isvalid import hash_password, verify_password
from werkzeug.security import generate_password_hash  
import os
app = Flask(__name__) 
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# ✅ सेशन सेटअप (Flask Session)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.secret_key = 'your_secret_key' 
def get_db_connection():
    conn = sqlite3.connect('majdur.db')
    conn.row_factory = sqlite3.Row
    return conn
@app.route('/')
def home():
    print("🏠 Home Page Session Data:", session)  # Debugging
    if 'username' not in session:
        return redirect('/login') 
    
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs').fetchall()
    conn.close()
    
    return render_template('home.html', jobs=jobs, username=session['username'])

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['number']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        hashed_password = hash_password(password) 
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (name, phone, email, username, password, role) VALUES (?, ?, ?, ?, ?, ?)', 
                         (name, phone, email, username, hashed_password, role))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists!"
        finally:
            conn.close()

        return redirect('/login')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and verify_password(user['password'], password):
            session['username'] = user['username']  
            session['user'] = user['username']  
            session['user_role'] = user['role']
            return redirect('/')
        else:
            flash(" Invalid Credentials", "danger")
            return redirect('/login')

    return render_template('log.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login') 
@app.route('/job_post', methods=['GET', 'POST'])
def job_post():
    print("Session Data:", session)  
    if 'user_role' not in session:
        return "Access Denied! User role missing."
    
    if session['user_role'] != 'employer':
        return "Access Denied! Only employers can post jobs."

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        salary = request.form['salary']
        category = request.form['category']
        employer = session.get('username', 'Unknown') 

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO jobs (title, description, location, salary, category, employer) VALUES (?, ?, ?, ?, ?, ?)',
            (title, description, location, salary, category, employer)
        )
        conn.commit()
        conn.close()

        return redirect('/')  
    return render_template('job_post.html')
@app.route('/job/<int:job_id>')
def job_details(job_id):
    conn = get_db_connection()
    job = conn.execute('SELECT jobs.*, users.name, users.phone, users.email FROM jobs JOIN users ON jobs.employer = users.username WHERE jobs.id = ?', (job_id,)).fetchone()
    conn.close()
    if not job:
        return "Job not found!", 404
    return render_template('job_details.html', job=job)
    
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()  
    conn = get_db_connection()

    
    jobs = conn.execute(
        "SELECT * FROM jobs WHERE title LIKE ? OR location LIKE ? OR category LIKE ?",
        (f"%{query}%", f"%{query}%", f"%{query}%")
    ).fetchall()

   
    users = conn.execute(
        "SELECT * FROM users WHERE name LIKE ? OR username LIKE ? OR phone LIKE ?",
        (f"%{query}%", f"%{query}%", f"%{query}%")
    ).fetchall()

    conn.close()
    
    return render_template('search_results.html', query=query, jobs=jobs, users=users)
@app.route('/user/<username>')
def user_profile(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not user:
        return "User not found!", 404

    return render_template('user_profile.html', user=user)
@app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):  # 🔹 यहाँ job_id URL से आ रहा है
    if 'username' not in session:
        return redirect(url_for('login'))  

    conn = get_db_connection()

    # ✅ अगर POST Request है → अपडेट करें
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        salary = request.form['salary']
        category = request.form['category']

        conn.execute("""
            UPDATE jobs 
            SET title = ?, description = ?, location = ?, salary = ?, category = ? 
            WHERE id = ?
        """, (title, description, location, salary, category, job_id))

        conn.commit()
        conn.close()

        flash("Job updated successfully!", "success")
        return redirect(url_for('account'))  

    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()

    if not job:
        return "Job not found!", 404

    return render_template('edit.html', job=job)
@app.route('/delete_job/<int:job_id>')
def delete_job(job_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    
    flash("Job deleted successfully!", "success")
    return  redirect('/')#(url_for('/job_details'))#,job_id=job_id))
@app.route('/account')
def account():
    if 'username' not in session:
        return redirect(url_for('login'))  # अगर यूज़र लॉगिन नहीं है तो लॉगिन पेज पर भेजो  

    username = session['username']  

    conn = get_db_connection()

    # यूज़र की बेसिक जानकारी `users` टेबल से लाना  
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    # यूज़र की प्रोफाइल डिटेल्स `user_profile` टेबल से लाना  
    profile_data = conn.execute("SELECT * FROM user_profile WHERE user_id = ?", (user['id'],)).fetchone()

    # यूज़र द्वारा पोस्ट की गई जॉब्स लाना  
    jobs = conn.execute("SELECT * FROM jobs WHERE employer=?", (username,)).fetchall()

    conn.close()

    if not user:
        return render_template('404.html'), 404  

    # प्रोफाइल डिटेल्स को एक डिक्शनरी में बदलना  
    user_profile = {}
    if profile_data:
        columns = [col[0] for col in conn.execute("PRAGMA table_info(user_profile)").fetchall()]
        user_profile = dict(zip(columns, profile_data))

    return render_template('account.html', user=user, user_profile=user_profile, jobs=jobs)
@app.route('/about')
def about():
	return render_template('about_us.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/send-email', methods=['POST'])
def send_email():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        
        msg = Message("नया संपर्क अनुरोध - Rojgar Setu",
                      sender=email,
                      recipients=['support@rojgarsetu.com'])
        msg.body = f"""
        📌 नाम: {name}
        📧 ईमेल: {email}
        📞 फोन: {phone}
        
        ✉️ संदेश:
        {message}
        """
        
        try:
            mail.send(msg)  
            flash("संदेश सफलतापूर्वक भेजा गया!", "success")
        except Exception as e:
            flash(f"कुछ गड़बड़ हो गई: {str(e)}", "danger")

        return redirect('/contact')
@app.route('/activity')
def activity():
	return render_template('activity.html')
@app.route('/instagram')
def instagram():
    return redirect("https://www.instagram.com/mai_sanyog_hu")  
@app.route('/delete-account')
def delete_account():
    if 'user_id' not in session:
        return redirect('/login')  
    
    user_id = session['user_id']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            print("User not found in database!")
            return "User not found!", 404
        
        
        cursor.execute("DELETE FROM posts WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM comments WHERE user_id = ?", (user_id,))
        
       
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

       
        session.pop('user_id', None)

        print("User deleted successfully!")
        return redirect('/')  
    except Exception as e:
        print("Error deleting user:", str(e))
        return "Error deleting account!", 500
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form['identifier']
        conn = sqlite3.connect('majdur.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR phone = ?", (identifier, identifier))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['reset_user'] = user[0]  
            return redirect(url_for('reset_password'))  
        else:
            flash('User not found!', 'danger')

    return render_template('forgot_password.html')
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_user' not in session:
        print("⚠️ reset_user not found in session, redirecting to forgot_password")
        return redirect(url_for('forgot_password'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        
        reset_user_id = session['reset_user']
        print(f" Checking if ID exists in DB: {reset_user_id}")

        cursor.execute("SELECT username FROM users WHERE id = ?", (reset_user_id,))
        user = cursor.fetchone()

        if user is None:
            print(f"ERROR: No user found with ID {reset_user_id}!")
            return redirect(url_for('forgot_password'))

        username = user[0]  
        print(f"Found Username: {username}")

    except Exception as e:
        print(f" Database Error: {e}")
        return redirect(url_for('forgot_password'))

    finally:
        conn.close()

    if request.method == 'POST':
        new_password = request.form['new_password']
        print(f"🔹 New Password Entered: {new_password}")

        hashed_password = generate_password_hash(new_password)
        print(f"🔹 Hashed Password: {hashed_password}")  # Debugging

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            
            cursor.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (hashed_password, username)
            )
            conn.commit()

            if cursor.rowcount > 0:
                print(f" SUCCESS: Password updated for {username} in majdur.db!")
            else:
                print("ERROR: Password update failed! No rows affected.")

        except Exception as e:
            print(f" Database Error: {e}")

        finally:
            conn.close()

        session.pop('reset_user', None)  # Clear session after reset
        flash("Password successfully updated!", "success")

        return redirect(url_for('login'))

    return render_template('reset_password.html')
    
    
@app.route('/chat_home')
def chat_home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', user=session['user'])

@app.route('/chat/search_users', methods=['GET'])
def chat_search_users():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.execute("SELECT username FROM users WHERE username LIKE ?", ('%' + query + '%',))
    users = [row['username'] for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(users)


@app.route('/chat/<receiver>')
def chat(receiver):
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', user=session['user'], receiver=receiver)


@app.route('/chat/send_message', methods=['POST'])
def chat_send_message():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 403 

    data = request.json
    sender = session['user']  
    receiver = data.get('receiver')
    message = data.get('message')

    if not receiver or not message.strip():
        return jsonify({"error": "Invalid data"}), 400  
    conn = get_db_connection()
    conn.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", (sender, receiver, message))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route('/chat/get_messages/<receiver>')
def chat_get_messages(receiver):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 403  
    sender = session['user']
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT sender, message FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY id ASC",
        (sender, receiver, receiver, sender)
    )
    messages = [{"sender": row['sender'], "message": row['message']} for row in cursor.fetchall()]
    conn.close()

    return jsonify({"messages": messages})
@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()

    # `users` टेबल से यूज़र की मौजूदा जानकारी प्राप्त करें
    user_data = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    # `user_profile` टेबल से डेटा प्राप्त करें
    user_profile = conn.execute("SELECT * FROM user_profile WHERE username = ?", (username,)).fetchone()

    # अगर `user_profile` टेबल में डेटा नहीं है, तो `users` टेबल का डेटा यूज़ करें
    if not user_profile:
        user_profile = {
            'full_name': user_data['name'] if user_data else '',
            'email': user_data['email'] if user_data else '',
            'phone': user_data['phone'] if user_data else '',
            'bio': '',
            'skills': '',
            'work_experience': '',
            'education': '',
            'job_status': '',
            'company': '',
            'designation': '',
            'linkedin': '',
            'github': '',
            'portfolio': '',
            'profile_photo': '',
            'resume': '',
            'id_proof': '',
            'language': '',
            'notification_preferences': ''
        }

    if request.method == 'POST':
        full_name = request.form.get('full_name', user_profile['full_name'])
        email = request.form.get('email', user_profile['email'])
        phone = request.form.get('phone', user_profile['phone'])
        bio = request.form.get('bio', user_profile['bio'])
        skills = request.form.get('skills', user_profile['skills'])
        work_experience = request.form.get('work_experience', user_profile['work_experience'])
        education = request.form.get('education', user_profile['education'])
        job_status = request.form.get('job_status', user_profile['job_status'])
        company = request.form.get('company', user_profile['company'])
        designation = request.form.get('designation', user_profile['designation'])
        linkedin = request.form.get('linkedin', user_profile['linkedin'])
        github = request.form.get('github', user_profile['github'])
        portfolio = request.form.get('portfolio', user_profile['portfolio'])
        language = request.form.get('language', user_profile['language'])
        notification_preferences = request.form.get('notification_preferences', user_profile['notification_preferences'])

        # Profile Photo Upload
        profile_photo = user_profile['profile_photo']
        if 'profile_photo' in request.files:
            photo_file = request.files['profile_photo']
            if photo_file.filename:
                profile_photo = f"uploads/{photo_file.filename}"
                photo_file.save(os.path.join('static/uploads', photo_file.filename))

        # Resume Upload
        resume = user_profile['resume']
        if 'resume' in request.files:
            resume_file = request.files['resume']
            if resume_file.filename:
                resume = f"uploads/{resume_file.filename}"
                resume_file.save(os.path.join('static/uploads', resume_file.filename))

        # ID Proof Upload
        id_proof = user_profile['id_proof']
        if 'id_proof' in request.files:
            id_proof_file = request.files['id_proof']
            if id_proof_file.filename:
                id_proof = f"uploads/{id_proof_file.filename}"
                id_proof_file.save(os.path.join('static/uploads', id_proof_file.filename))

        # अगर पहले से डेटा मौजूद है, तो अपडेट करें
        if conn.execute("SELECT * FROM user_profile WHERE username = ?", (username,)).fetchone():
            conn.execute("""UPDATE user_profile SET 
                full_name=?, email=?, phone=?, bio=?, skills=?, work_experience=?, education=?, job_status=?, company=?, designation=?, 
                linkedin=?, github=?, portfolio=?, profile_photo=?, resume=?, id_proof=?, language=?, notification_preferences=? 
                WHERE username=?""",
                (full_name, email, phone, bio, skills, work_experience, education, job_status, company, designation, 
                 linkedin, github, portfolio, profile_photo, resume, id_proof, language, notification_preferences, username))
        else:
            # अगर डेटा मौजूद नहीं है, तो नया डेटा इंसर्ट करें
            conn.execute("""INSERT INTO user_profile 
                (username, full_name, email, phone, bio, skills, work_experience, education, job_status, company, designation, 
                linkedin, github, portfolio, profile_photo, resume, id_proof, language, notification_preferences) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (username, full_name, email, phone, bio, skills, work_experience, education, job_status, company, designation, 
                 linkedin, github, portfolio, profile_photo, resume, id_proof, language, notification_preferences))

        conn.commit()
        conn.close()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('account'))

    return render_template('profile.html', user_profile=user_profile)
if __name__ == '__main__':
    app.run(debug=True)
	    
