import yfinance as yf
import mysql.connector
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

        if user and user[3] == password:               # User exists, pw matches
            session['email'] = email  
            return redirect(url_for('portfolio'))
        else:
            return "Invalid credentials"

    return render_template('login.html')


# Portfolio route
@app.route('/portfolio', methods=['GET'])
def portfolio():
    if 'email' not in session:                  # If user not logged in
        return redirect(url_for('login'))

    email = session['email']            
    cursor = mysql_conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))       # Query to get userid based on email
    userid = cursor.fetchone()[0]
    cursor.close()

                            # Fetch all transactions for the user
    cursor = mysql_conn.cursor()
    cursor.execute("SELECT ticker, purchase_date, amount FROM transactions WHERE userid = %s", (userid,))  # Query to get all transactions
    transactions = cursor.fetchall()
    cursor.close()

    portfolio_summary = {}         #Init
    total_portfolio_value = 0
    total_invested_value = 0    

    for transaction in transactions:    # Loop each transactions
        ticker = transaction[0]
        amount = transaction[2]

                             # Fetch historical price at the purchase date
        stock = yf.Ticker(ticker)
        purchase_date = transaction[1]          # Historical date to calculate purchase date price
        history = stock.history(start=purchase_date, end=purchase_date + timedelta(days=1))
        invested_value = float(amount) * history.iloc[0]['Close'] if not history.empty else 0

                            # Fetch the current stock price
        current_data = stock.history(period="1d")       # Current date to calculate current price
        current_value = float(amount) * current_data.iloc[-1]['Close'] if not current_data.empty else 0

                            # Calculate profit/loss
        profit_loss = current_value - invested_value

                            # Sum transactions for the same ticker
        if ticker in portfolio_summary:                         # If user buys same stock more times
            portfolio_summary[ticker]['total_amount'] += amount         # Update, increment amount etc...
            portfolio_summary[ticker]['invested_value'] += invested_value
            portfolio_summary[ticker]['total_value'] += current_value
            portfolio_summary[ticker]['profit_loss'] += profit_loss
        else:
            portfolio_summary[ticker] = {           # If the stock new in the prtfolio
                'ticker': ticker,
                'total_amount': amount,
                'invested_value': invested_value,
                'total_value': current_value,
                'profit_loss': profit_loss
            }

                             # Add to the overall totals
        total_portfolio_value += current_value
        total_invested_value += invested_value          # Add to total invested value

                             # Calculate CGT
    total_profit = total_portfolio_value - total_invested_value

    cgt_threshold = 1270  # CGT exemption
    cgt_rate = 0.33  # CGT rate

    if total_profit > cgt_threshold:
        taxable_profit = total_profit - cgt_threshold
        capital_gains_tax = taxable_profit * cgt_rate
    else:
        capital_gains_tax = 0  # No tax below threshold

    total_stock_values = list(portfolio_summary.values())

    return render_template('portfolio.html', total_stock_values=total_stock_values,     # Passed to portfolio web
                           total_portfolio_value=total_portfolio_value,
                           total_invested_value=total_invested_value,
                           total_profit=total_profit,
                           capital_gains_tax=capital_gains_tax)

# Tickers route (tickers to database)
@app.route('/tickers', methods=['GET', 'POST'])
def tickers():
    email = session['email']
    
                                # Reconnect if no connection
    if not mysql_conn.is_connected():                           #*****************************************************************
        mysql_conn.reconnect(attempts=3, delay=5)

    if request.method == 'GET':
                                # Fetch tickers for the user
        cursor = mysql_conn.cursor()
        cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))       # Query to get userid based on email
        userid = cursor.fetchone()[0]  
        cursor.close()

        cursor = mysql_conn.cursor()
        cursor.execute("SELECT ticker FROM user_portfolio WHERE userid = %s", (userid,))        # Query to get ticker
        user_tickers = cursor.fetchall()
        cursor.close()

        whatever = {'tickers': [ticker[0] for ticker in user_tickers]}              # Dict, list of tickers
        return jsonify(whatever)
    
    elif request.method == 'POST':
                                                # Add a new ticker to portfolio
        content = request.json
        new_ticker = content.get('ticker')

        cursor = mysql_conn.cursor()
        cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))       # Query to get userid based on email
        userid = cursor.fetchone()[0]

                                                # Insert the new ticker into the user's portfolio
        cursor.execute("INSERT INTO user_portfolio (userid, ticker) VALUES (%s, %s)", (userid, new_ticker))     # Query add new ticker
        mysql_conn.commit()
        cursor.close()

        return jsonify({'result': 'success'})

# Remove tickers route (Remove tickers from database)
@app.route('/remove_ticker', methods=['POST'])
def remove_ticker():
    if 'email' not in session:                              # If user not logged in
        return jsonify({'error': 'Unauthorized'}), 403
    
    email = session['email']                
    content = request.json
    ticker = content.get('ticker')

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))       # Query to get userid based on email
    userid = cursor.fetchone()[0]

    cursor.execute("DELETE FROM user_portfolio WHERE userid = %s AND ticker = %s", (userid, ticker))        # Query remove ticker
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
    if request.method == 'POST':                            # User submits register form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:                    # Checking password match
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

    return render_template('register.html')             # Registration for rendered if GET method

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
        date_of_birth = user_details[1].strftime('%Y-%m-%d')        # 
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

# Get stock data route (Fetch historical price using Yahoo)
@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    ticker = request.json['ticker']                     # Extract the value ticker from json data
    data = yf.Ticker(ticker).history(period='1y')               # Check "1y" options later
    return jsonify({'currentPrice': data.iloc[-1].Close,
                    'openPrice': data.iloc[-1].Open})
# reference: NeuralNine - Real-Time Stock Price Tracker in Python https://youtu.be/GSHFzqqPq5U?list=PLF6w5cpj_zBo6dTD4avNwz1xbqYRiKBsN

# Add transaction route
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'email' not in session:                          # If user not logged in
        return jsonify({'error': 'Unauthorized'}), 403

    email = session['email']                    # If user not logged in
    content = request.json
    ticker = content.get('ticker')
    purchase_date = content.get('purchase_date')
    amount = content.get('amount')

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))       # Query to get userid based on email
    userid = cursor.fetchone()[0]

    cursor.execute("INSERT INTO transactions (userid, ticker, purchase_date, amount) VALUES (%s, %s, %s, %s)", (userid, ticker, purchase_date, amount)) # Query insert transact to DB
    mysql_conn.commit()
    cursor.close()

    return jsonify({'result': 'success'})

# Get transactions route
@app.route('/get_transactions', methods=['GET'])
def get_transactions():
    if 'email' not in session:                              # If user not logged in
        return jsonify({'error': 'Unauthorized'}), 403

    email = session['email']                    
    
    if not mysql_conn.is_connected():
        mysql_conn.reconnect(attempts=3, delay=5)

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))       # Query to get userid based on email
    userid = cursor.fetchone()[0]

    cursor.close()                      # Close the first cursor

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT ticker, purchase_date, amount FROM transactions WHERE userid = %s", (userid,))       # Query to get transactions based on userid
    transactions = cursor.fetchall()
    cursor.close()                      # Close the second cursor

    result = [{'ticker': t[0], 'purchase_date': t[1].strftime('%Y-%m-%d'), 'amount': t[2]} for t in transactions]       # List of tuples, convert datetime
    return jsonify(result)

# Get historical price
@app.route('/get_historical_price', methods=['POST'])
def get_historical_price():
    content = request.json
    ticker = content.get('ticker')
    purchase_date = content.get('purchase_date')

                            # Convert datetime to Yahoo 
    date = datetime.strptime(purchase_date, '%Y-%m-%d')

                            # Fetch the historical data Yahoo
    stock = yf.Ticker(ticker)
    history = stock.history(start=date, end=date + timedelta(days=1))           # Fetch data for specific day

    if not history.empty:
        unit_price = history.iloc[0]['Close']                                   # Get the closing price
    else:
        unit_price = 0                                      # 0 if no data is found

    return jsonify({'unitPrice': unit_price})

# Remove transaction from the DB
@app.route('/remove_transaction', methods=['POST'])
def remove_transaction():
    if 'email' not in session:                              # If user not logged in
        return jsonify({'error': 'Unauthorized'}), 403

    email = session['email']
    content = request.json
    ticker = content.get('ticker')
    purchase_date = content.get('purchase_date')

    cursor = mysql_conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE email = %s", (email,))           # Query to get userid based on email
    userid = cursor.fetchone()[0]

    cursor.execute("DELETE FROM transactions WHERE userid = %s AND ticker = %s AND purchase_date = %s", # Query to delete transaction
                   (userid, ticker, purchase_date))
    mysql_conn.commit()
    cursor.close()

    return jsonify({'result': 'success'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

