from flask import Flask, render_template, request, redirect, session,flash
from flask_mail import Mail, Message  # ✅ इसे इम्पोर्ट करें
import sqlite3
from isvalid import hash_password,verify_password
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Gmail SMTP Server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'rojgarsetu7@gmail.com'  # अपना ईमेल डालें
app.config['MAIL_PASSWORD'] = 'rojgarsetu7@gmail.com'  # अपना पासवर्ड डालें
app.config['MAIL_DEFAULT_SENDER'] = 'rojgarsetu7@gmail.com'  # Sender Email
mail = Mail(app)

def get_db_connection():
    conn = sqlite3.connect('majdur.db')
    conn.row_factory = sqlite3.Row
    return conn

# **Home Route (Dashboard)**
@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/login')  # अगर यूजर लॉगिन नहीं है तो लॉगिन पेज पर भेजो
    
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

        if user:
            stored_password = user['password']
            print(f"Stored Password: {stored_password}")  # Debugging
            print(f"Entered Password: {password}")  # Debugging

            # **Check if stored password is plain text or hashed**
            if stored_password.startswith("scrypt") or stored_password.startswith("pbkdf2"):  
                # Hashed password verification
                if verify_password(stored_password, password):
                    session['username'] = user['username']
                    session['user_role'] = user['role']
                    return redirect('/')
                else:
                    return "Invalid Credentials"
            else:
                # **If plain text, hash it and update in the database**
                new_hashed_password = hash_password(stored_password)
                conn = get_db_connection()
                conn.execute("UPDATE users SET password = ? WHERE username = ?", (new_hashed_password, username))
                conn.commit()
                conn.close()
                print("🔄 Password hashed and updated in database!")

                # **Now verify the new hashed password**
                if verify_password(new_hashed_password, password):
                    session['username'] = user['username']
                    session['user_role'] = user['role']
                    return redirect('/')
                else:
                    return "Invalid Credentials"

    return render_template('log.html')
# **Logout Route**
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

@app.route('/chat')
def chat():
	return render_template('chat.html')
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
if __name__ == '__main__':
    app.run(debug=True)
