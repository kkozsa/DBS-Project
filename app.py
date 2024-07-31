import yfinance as yf
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, jsonify, session

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = b'11223344'

                                                        # Database config
mysql_host = 'localhost'
mysql_user = 'sqluser'
mysql_password = '123456789'
mysql_db = 'sandc_db'

                                                        # Connect to MySQL
mysql_conn = mysql.connector.connect(
    host=mysql_host,
    user=mysql_user,
    password=mysql_password,
    database=mysql_db
)

                                                        # Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql_conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and user[3] == password:  # Assuming password is the 4th field
            session['email'] = email  # Store user's email in session
            return redirect(url_for('portfolio'))
        else:
            return "Invalid credentials"

    return render_template('login.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/transactions')
def transactions():
    return render_template('transactions.html')

@app.route('/logout')
def logout():
    session.clear()                         # Clear the session to remove user data
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return "Passwords do not match!"

        cursor = mysql_conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            return "User with this email already exists!"

        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        mysql_conn.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/profile')
def profile():
    email = session.get('email')  # Retrieve user's email from session
    return render_template('profile.html', email=email)


@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    ticker = request.json['ticker']
    data = yf.Ticker(ticker).history(period='1y')
    return jsonify({'currentPrice': data.iloc[-1].Close,
                    'openPrice': data.iloc[-1].Open})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

