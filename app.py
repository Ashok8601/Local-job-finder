from flask import Flask, render_template, request, redirect,session
import sqlite3

app = Flask(__name__)
app.secret_key ='your_name'
# Database Connection Function
def get_db_connection():
    conn = sqlite3.connect('majdur.db')
    conn.row_factory = sqlite3.Row
    return conn

# Signup Page
@app.route('/')
def home():
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs').fetchall()
    conn.close()
    return render_template('home.html', jobs=jobs)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['number']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        '''confirm_password = request.form['confirm_password']'''
        role = request.form['role']
        '''location = request.form['location']
        skills = request.form.get('skills', '')  # Optional field
        experience = request.form.get('experience', 0)  # Default 0 if empty
        company_name = request.form.get('company_name', '')  # Only for employers
        '''
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (name,phone,email,username, password,role) VALUES (?, ?, ?,?,?,?)', 
                         (name,phone,email,username, password, role))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists!"
        finally:
            conn.close()

        return redirect('/login')  # Signup success, redirect to login

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                            (username, password)).fetchone()
        conn.close()
        if user:
            session['username'] = user['username']
            session['user_role'] = user['role']  # यूज़र का रोल स्टोर करें
            return redirect('/')
        else:
            return "Invalid Credentials"

    return render_template('log.html')
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

        return redirect('/home')  # Successfully insert hone ke baad redirect
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
if __name__ == '__main__':
    app.run(debug=True)
