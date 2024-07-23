
// DATABASE  //

const express = require('express');
const mysql = require('mysql2');
const bodyParser = require('body-parser');

const app = express();

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Frontend directory
app.use(express.static(__dirname + '/../templates'));

// MySQL connection
const db = mysql.createConnection({
    host: 'localhost',
    user: 'sqluser',                                        
    password: '123456789',                                  
    database: 'sandc_db'
});

// Check if database connected                              
db.connect((err) => {
    if (err) {
        console.error('Error connecting to database:', err);
        return;
    }
    console.log('Connected to database successfully');
});

app.post('/register', (req, res) => {
    const { username, email, password, password2 } = req.body;

    if (!email || !password) {
        return res.status(400).send('Email and password are required');
    }

    // Check if it is a registration or login attempt
    if (username) {
        
        // Signup logic

        if (!password2) {
            return res.status(400).send('Confirmation password is required');
        }
        if (password !== password2) {
            return res.status(400).send('Passwords do not match');
        }
                
        db.query('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', [username, email, password], (err, result) => {
            if (err) {
                console.error('Error inserting data into database:', err);
                return res.status(500).send('Internal Server Error');
            }
            console.log('User registered successfully:', result);
            res.status(200).send('User registered successfully');
        });
    } else {

        // Signin logic

        db.query('SELECT * FROM users WHERE email = ? AND password = ?', [email, password], (err, results) => {
            if (err) {
                console.error('Error querying database:', err);
                return res.status(500).send('Internal Server Error');
            }

            if (results.length === 0) {
                return res.status(401).send('Invalid email or password');
            }

            console.log('User signed in successfully:', results[0]);
            res.status(200).send('User signed in successfully');
        });
    }
});

app.use((req, res) => {
    res.status(404).send('<h1>Error 404: Resource not found</h1>')
})
//console.log("Attempting to listening on port 5555.")
app.listen(5555, ()=> {
    console.log("Listening on port 5555.")
});
