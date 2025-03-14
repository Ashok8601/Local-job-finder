from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from flask_mail import Mail, Message  
from datetime import timedelta
from flask_session import Session
import sqlite3
from isvalid import hash_password, verify_password
from werkzeug.security import generate_password_hash  

app = Flask(__name__)  # ✅ सबसे पहले `app` डिफाइन करें

# ✅ सेशन सेटअप (Flask Session)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.secret_key = 'your_secret_key'  # ✅ सीक्रेट की सेट करें

# ✅ Flask-Mail सेटअप (ईमेल भेजने के लिए)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'rojgarsetu7@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password_here'  # ⚠️ यहां Gmail का ऐप पासवर्ड डालें (सीधा ईमेल पासवर्ड नहीं)
app.config['MAIL_DEFAULT_SENDER'] = 'rojgarsetu7@gmail.com'
mail = Mail(app)
def get_db_connection():
    conn = sqlite3.connect('majdur.db')
    conn.row_factory = sqlite3.Row
    return conn

# **Home Route (Dashboard)**
@app.route('/')
def home():
    print("🏠 Home Page Session Data:", session)  # Debugging
    if 'username' not in session:
        return redirect('/login') 
    
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs').fetchall()
    conn.close()
    
    return render_template('home.html', jobs=jobs, username=session['username'])

# **Signup Route (Password Hashing के साथ)**
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['number']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        hashed_password = hash_password(password)  # पासवर्ड हैश करना

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

# **Login Route (Password Verification 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and verify_password(user['password'], password):
            session['username'] = user['username']  # ✅ Ensure this key is consistent
            session['user'] = user['username']  # ✅ Add this for chat compatibility
            session['user_role'] = user['role']
            return redirect('/')
        else:
            flash("❌ Invalid Credentials", "danger")
            return redirect('/login')

    return render_template('log.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')  # लॉगआउट के बाद लॉगिन पेज पर भेजो
@app.route('/job_post', methods=['GET', 'POST'])
def job_post():
    print("Session Data:", session)  # Debugging ke liye

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
        employer = session.get('username', 'Unknown')  # Default agar username missing ho

        conn = get_db_connection()  # Database connection
        conn.execute(
            'INSERT INTO jobs (title, description, location, salary, category, employer) VALUES (?, ?, ?, ?, ?, ?)',
            (title, description, location, salary, category, employer)
        )
        conn.commit()
        conn.close()

        return redirect('/')  # Successfully insert hone ke baad redirect
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
    query = request.args.get('q', '').strip()  # User ka search query
    conn = get_db_connection()

    # Jobs Search Query
    jobs = conn.execute(
        "SELECT * FROM jobs WHERE title LIKE ? OR location LIKE ? OR category LIKE ?",
        (f"%{query}%", f"%{query}%", f"%{query}%")
    ).fetchall()

    # Users Search Query
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
    
@app.route('/account')
def account():
    if 'username' not in session:
        return redirect(url_for('login'))  # 🔹 अगर लॉगिन नहीं किया, तो लॉगिन पेज पर भेजें

    username = session['username']  # 🔹 Session से यूज़रनेम लेना

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    
    if not user:
        return render_template('404.html'), 404  # 🔹 अगर यूज़र नहीं मिला, तो 404 पेज

    return render_template('account.html', user=user)
@app.route('/about')
def about():
	return render_template('about_us.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')

# 🔹 Email Send Route
@app.route('/send-email', methods=['POST'])
def send_email():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        # 🔹 ईमेल भेजने के लिए मैसेज तैयार करें
        msg = Message("नया संपर्क अनुरोध - Rojgar Setu",
                      sender=email,
                      recipients=['support@rojgarsetu.com'])  # Admin Email

        msg.body = f"""
        📌 नाम: {name}
        📧 ईमेल: {email}
        📞 फोन: {phone}
        
        ✉️ संदेश:
        {message}
        """
        
        try:
            mail.send(msg)  # 🔹 ईमेल भेजें
            flash("संदेश सफलतापूर्वक भेजा गया!", "success")
        except Exception as e:
            flash(f"कुछ गड़बड़ हो गई: {str(e)}", "danger")

        return redirect('/contact')
@app.route('/activity')
def activity():
	return render_template('activity.html')
@app.route('/instagram')
def instagram():
    return redirect("https://www.instagram.com/mai_sanyog_hu")  # अपना इंस्टाग्राम यूज़रनेम डालें
@app.route('/delete-account')
def delete_account():
    if 'user_id' not in session:
        return redirect('/login')  # 🔹 अगर यूज़र लॉगिन नहीं है, तो लॉगिन पेज पर भेजें
    
    user_id = session['user_id']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 🔹 Debugging: Check User Exists
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            print("User not found in database!")
            return "User not found!", 404
        
        # 🔹 अगर यूज़र की अन्य टेबल्स में एंट्री है, पहले डिलीट करें
        cursor.execute("DELETE FROM posts WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM comments WHERE user_id = ?", (user_id,))
        
        # 🔹 अब यूज़र डिलीट करें
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        # 🔹 सेशन क्लियर करें
        session.pop('user_id', None)

        print("User deleted successfully!")
        return redirect('/')  # 🔹 Home Page पर Redirect करें
    
    except Exception as e:
        print("Error deleting user:", str(e))
        return "Error deleting account!", 500
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form['identifier']  # Yeh username ya phone number ho sakta hai
        
        conn = sqlite3.connect('majdur.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR phone = ?", (identifier, identifier))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['reset_user'] = user[0]  # User ID ko session me store kar rahe hain
            return redirect(url_for('reset_password'))  # Reset password page pe bhej rahe hain
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
        
        # ✅ Check if session value is ID instead of username
        reset_user_id = session['reset_user']
        print(f"🔍 Checking if ID exists in DB: {reset_user_id}")

        cursor.execute("SELECT username FROM users WHERE id = ?", (reset_user_id,))
        user = cursor.fetchone()

        if user is None:
            print(f"❌ ERROR: No user found with ID {reset_user_id}!")
            return redirect(url_for('forgot_password'))

        username = user[0]  # ✅ Correct username fetched
        print(f"✅ Found Username: {username}")

    except Exception as e:
        print(f"❌ Database Error: {e}")
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

            # ✅ Update Query with Correct Username
            cursor.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (hashed_password, username)
            )
            conn.commit()

            if cursor.rowcount > 0:
                print(f"✅ SUCCESS: Password updated for {username} in majdur.db!")
            else:
                print("❌ ERROR: Password update failed! No rows affected.")

        except Exception as e:
            print(f"❌ Database Error: {e}")

        finally:
            conn.close()

        session.pop('reset_user', None)  # Clear session after reset
        flash("✅ Password successfully updated!", "success")

        return redirect(url_for('login'))

    return render_template('reset_password.html')
    
    # chat implementation

# ✅ Chat Home (Avoid conflict with existing 'home' route)
@app.route('/chat_home')
def chat_home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', user=session['user'])
# ✅ Search Users (Unique route)
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

# ✅ Chat with a specific user (Avoids conflict with existing routes)
@app.route('/chat/<receiver>')
def chat(receiver):
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', user=session['user'], receiver=receiver)

# ✅ Send Message
@app.route('/chat/send_message', methods=['POST'])
def chat_send_message():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 403  # ✅ Unauthorized users को ब्लॉक करो

    data = request.json
    sender = session['user']  # ✅ सेशन से यूज़र लो
    receiver = data.get('receiver')
    message = data.get('message')

    if not receiver or not message.strip():
        return jsonify({"error": "Invalid data"}), 400  # ✅ सही डेटा ना हो तो एरर दो

    conn = get_db_connection()
    conn.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", (sender, receiver, message))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# ✅ Fetch Messages
@app.route('/chat/get_messages/<receiver>')
def chat_get_messages(receiver):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 403  # ✅ अगर सेशन में यूज़र नहीं है तो एरर दो

    sender = session['user']
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT sender, message FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY id ASC",
        (sender, receiver, receiver, sender)
    )
    messages = [{"sender": row['sender'], "message": row['message']} for row in cursor.fetchall()]
    conn.close()

    return jsonify({"messages": messages})
# ✅ Login (Avoid conflict with existing 'login' route)
'''@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        session['user'] = username  # ⚠️ Use proper authentication in production
        return redirect(url_for('chat_home'))
    return render_template('log.html')

# ✅ Logout (Unique route to avoid conflict)
@app.route('/user_logout')
def user_logout():
    session.pop('user', None)
    return redirect(url_for('user_login'))'''
if __name__ == '__main__':
    app.run(debug=True)
