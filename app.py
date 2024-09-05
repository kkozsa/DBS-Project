import yfinance as yf
import mysql.connector
from decimal import Decimal
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, session

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = b'11223344'

# Database config
mysql_host = 'localhost'
mysql_user = 'sqluser'
#mysql_user = 'web'               # Uncomment for Azure            
mysql_password = '123456789'
mysql_db = 'sandc_db'
#mysql_password=open(".pass").readline().strip()          #input('Enter mySQL password: ')      # Uncomment for Azure 

# Connect to MySQL
mysql_conn = mysql.connector.connect(
    host=mysql_host,
    user=mysql_user,
    password=mysql_password,
    database=mysql_db
)

# Main route
@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':                    # User submits login form
        email = request.form['email']
        password = request.form['password']

        cursor = mysql_conn.cursor()                # Cursor interacts with DB
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))        # Query
        user = cursor.fetchone()
        cursor.close()

        if user and user[3] == password:  
            session['email'] = email  
            return redirect(url_for('portfolio'))
        else:
            return "Invalid credentials"

    return render_template('login.html')

# Portfolio route
@app.route('/portfolio', methods=['GET', 'POST'])                   
def portfolio():
    if 'email' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))

    email = session['email']
    
    # Fetch the user's ID
    cursor = mysql_conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))
    userid = cursor.fetchone()[0]

    # Fetch total amounts of each stock from transactions
    cursor.execute("""
        SELECT ticker, purchase_date, SUM(amount) as total_amount
        FROM transactions 
        WHERE userid = %s 
        GROUP BY ticker, purchase_date
    """, (userid,))
    total_amounts = cursor.fetchall()

    total_stock_values = []

    for ticker, purchase_date, total_amount in total_amounts:
        # Convert total_amount to float
        total_amount = float(total_amount)

        # Ensure purchase_date is in 'YYYY-MM-DD' format
        purchase_date_str = purchase_date.strftime('%Y-%m-%d')

        # Try to fetch data for the purchase date, move to previous date if no data
        purchase_date_obj = datetime.strptime(purchase_date_str, '%Y-%m-%d')

        # Try fetching data for the last available trading day if no data on purchase date
        for _ in range(7):  # Limit to trying the last 7 days to avoid infinite loops
            stock_data = yf.Ticker(ticker).history(start=purchase_date_obj.strftime('%Y-%m-%d'), end=(purchase_date_obj + timedelta(days=1)).strftime('%Y-%m-%d'))
            if not stock_data.empty:
                purchase_price = stock_data['Close'].iloc[0]
                break
            purchase_date_obj -= timedelta(days=1)  # Move to the previous day
        else:
            # If no data found, set purchase price to 0
            purchase_price = 0

        # Fetch current stock price for the total value
        current_stock_data = yf.Ticker(ticker).history(period='1d')
        current_price = current_stock_data['Close'].iloc[-1]

        # Calculate values
        invested_value = purchase_price * total_amount
        total_value = current_price * total_amount
        profit_loss = total_value - invested_value

        # Append to total_stock_values, including purchase_date
        total_stock_values.append({
            'ticker': ticker,
            'purchase_date': purchase_date_str,  # Add purchase date
            'total_amount': total_amount,
            'invested_value': invested_value,
            'total_value': total_value,
            'profit_loss': profit_loss
        })
    cursor.close()

    return render_template('portfolio.html', 
                           total_stock_values=total_stock_values)


# Tickers route (tickers to database)
@app.route('/tickers', methods=['GET'])                                                 
def tickers():
    email = session['email']
    
    # Reconnect logic in case the connection has been lost
    if not mysql_conn.is_connected():
        mysql_conn.reconnect(attempts=3, delay=5)

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))
    userid = cursor.fetchone()[0]  

    cursor.close()  # Close the first cursor

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT ticker FROM user_portfolio WHERE userid = %s", (userid,))
    user_tickers = cursor.fetchall()
    cursor.close()  # Close the second cursor
    
    whatever = {'tickers': [ticker[0] for ticker in user_tickers]}
    return jsonify(whatever)

# Remove tickers route (Remove tickers from database)
@app.route('/remove_ticker', methods=['POST'])
def remove_ticker():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    email = session['email']
    content = request.json
    ticker = content.get('ticker')

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))
    userid = cursor.fetchone()[0]

    cursor.execute("DELETE FROM user_portfolio WHERE userid = %s AND ticker = %s", (userid, ticker))
    mysql_conn.commit()
    cursor.close()

    return jsonify({'result': 'success'})

# Transaction route (delete or improve later)
@app.route('/transactions')
def transactions():
    return render_template('transactions.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()                         # Clear user data
    return redirect(url_for('login'))

# Register route (Register details to database)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':                    # User submits register form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:            # Checking password match
            return "Passwords do not match!"

        cursor = mysql_conn.cursor()                        # Cursor interacts with DB
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))        # Query
        existing_user = cursor.fetchone()                               # Check if user already exists by email

        if existing_user:
            cursor.close()
            return "User with this email already exists!"

        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))    # Query inserts into user table
        mysql_conn.commit()
        cursor.close()

        return redirect(url_for('login'))               # Back to login page   Maybe change to INDEX

    return render_template('register.html')             # Registration form rendered if GET method

# Profile route (Profile details to database)
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'email' not in session:                          # Check if the user already logged in
        return redirect(url_for('login'))

    email = session['email']                            
    
    if request.method == 'POST':                        # User submits profile form
        full_name = request.form['full_name']
        date_of_birth = request.form['date_of_birth']
        phone_number = request.form['phone_number']
        address = request.form['address']

        cursor = mysql_conn.cursor()                    # Cursor interacts with DB
        cursor.execute("""
            UPDATE users SET full_name = %s, date_of_birth = %s, phone_number = %s, address = %s        
            WHERE email = %s
        """, (full_name, date_of_birth, phone_number, address, email))      # Profile updated in DB if email matches.
        mysql_conn.commit()
        cursor.close()

        return redirect(url_for('profile'))
    
    cursor = mysql_conn.cursor()                    # Get to fetch profile information
    cursor.execute("SELECT full_name, date_of_birth, phone_number, address FROM users WHERE email = %s", (email,))      # Profile fetch from DB if email matches.
    user_details = cursor.fetchone()
    cursor.close()

    if user_details[1]:                                             # Format date_of_birth to YYYY-MM-DD
        date_of_birth = user_details[1].strftime('%Y-%m-%d')        
    else:
        date_of_birth = ""                                          # If not exists, set to empty string

    user = {                                                        # Dictionary for user profile information
        'full_name': user_details[0],
        'date_of_birth': date_of_birth,
        'phone_number': user_details[2],
        'address': user_details[3]
    }

    return render_template('profile.html', user=user)
# reference: Login and Registration Project Using Flask and MySQL https://www.geeksforgeeks.org/login-and-registration-project-using-flask-and-mysql/
# reference: How to get Data from MySQL DB on Python Flask? https://stackoverflow.com/questions/72608413/how-to-get-data-from-mysql-db-on-python-flask

# Get stock data route (Fetch historical stock price using yahoo finance)

@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    content = request.json
    ticker = content['ticker']
    purchase_date = content.get('purchase_date')

    if purchase_date:
        # Convert the purchase_date string to a datetime object
        purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d')

        # Try to fetch data for the given date, if no data, fetch for the previous available date
        for _ in range(7):  # Limit to trying the last 7 days to avoid infinite loops
            data = yf.Ticker(ticker).history(start=purchase_date_obj.strftime('%Y-%m-%d'), end=(purchase_date_obj + timedelta(days=1)).strftime('%Y-%m-%d'))
            if not data.empty:
                break
            # Move to the previous day
            purchase_date_obj -= timedelta(days=1)
        else:
            return jsonify({'error': 'No data found for this date'}), 404
    else:
        # Fetch the latest data if no date is provided
        data = yf.Ticker(ticker).history(period='1d')
    
    if data.empty:
        return jsonify({'error': 'No data found'}), 404

    # Get the closing price for the date
    closing_price = data['Close'].iloc[0]
    open_price = data['Open'].iloc[0]

    return jsonify({'currentPrice': closing_price, 'openPrice': open_price})

# reference: NeuralNine - Real-Time Stock Price Tracker in Python https://youtu.be/GSHFzqqPq5U?list=PLF6w5cpj_zBo6dTD4avNwz1xbqYRiKBsN

# Add transaction route
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    email = session['email']
    content = request.json
    ticker = content.get('ticker')
    purchase_date = content.get('purchase_date')
    amount = content.get('amount')

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))
    userid = cursor.fetchone()[0]

    cursor.execute("INSERT INTO transactions (userid, ticker, purchase_date, amount) VALUES (%s, %s, %s, %s)", (userid, ticker, purchase_date, amount))
    mysql_conn.commit()
    cursor.close()

    return jsonify({'result': 'success'})

# Get transactions route
@app.route('/get_transactions', methods=['GET'])
def get_transactions():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    # Ensure MySQL connection is active
    if not mysql_conn.is_connected():
        mysql_conn.reconnect(attempts=3, delay=5)

    # First, fetch the user's ID
    cursor = mysql_conn.cursor(buffered=True)  # Use a buffered cursor to avoid the unread result issue
    cursor.execute("SELECT userid FROM users WHERE email = %s", (session['email'],))
    userid = cursor.fetchone()[0]
    cursor.close()  # Close the first cursor

    # Now, fetch the transactions for the user
    cursor = mysql_conn.cursor(buffered=True)
    cursor.execute("SELECT ticker, purchase_date, amount FROM transactions WHERE userid = %s", (userid,))
    transactions = cursor.fetchall()  # Fetch all the results so no unread results remain
    cursor.close()

    result = [{'ticker': t[0], 'purchase_date': t[1].strftime('%Y-%m-%d'), 'amount': t[2]} for t in transactions]
    return jsonify(result)

@app.route('/get_total_amounts', methods=['GET'])
def get_total_amounts():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    email = session['email']
    cursor = mysql_conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))
    userid = cursor.fetchone()[0]

    cursor.execute("""
        SELECT ticker, SUM(amount) as total_amount 
        FROM transactions 
        WHERE userid = %s 
        GROUP BY ticker
    """, (userid,))
    total_amounts = cursor.fetchall()
    cursor.close()

    total_amounts_dict = [{'ticker': row[0], 'total_amount': row[1]} for row in total_amounts]
    return jsonify({'total_amounts': total_amounts_dict})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')