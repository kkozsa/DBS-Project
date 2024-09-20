S&C Portfolio Information System:
The primary aim of the S&C Portfolio Information System project is to develop a web based application, which allows users to manage their portfolio effectively. Users can register, login, add / remove financial assets they interested in and monitor those assets price in real-time. Users will also be able to add purchase / sell data input. Capital gains tax calculations will also be implemented based on those data.

Features:

Portfolio management:
The main functionality of the system is portfolio management, where users can track their investments and check real-time asset prices. Users allow to customize their watchlist, where they can add or remove assets, they interested in. The back-end uses Flask to handle these user requests while MySQL stores those asset tickers in the Portfolio table in the database. The front-end is dynamically updated using AJAX requests to provide real-time asset information via Yahoo Finance API.

Transaction management:
The user can add transaction inputs such as asset ticker, purchase date and amount of assets purchased. These data are stored in the transaction table in the database. Yahoo Finance API fetches the actual price of the purchase date and updates portfolio value and profit / loss. 

Yahoo Finance API:
Yahoo Finance API library is used to fetch historical and real-time asset data. Every time a user views the portfolio page, the back-end fetches the latest asset prices for all the tickers in the portfolio of the user. Historical prices are used to calculate the value of the past transactions, while the real-time prices are used to calculate the latest portfolio value and profit / loss.

Profit / loss calculation:

The profit / loss are calculated by the comparison of the assets purchase price and current price, multiplied by the overall asset held by the user. The calculation is done in the back-end and sent to the front-end. 


Technology used:
Frontend: HTML, CSS, Bootstrap, Javascript.

Backend: Python Flask, Javascript, MySQL.

External APIs: Alphavantage, Polygon, Yahoo Finance. External APIs were tested in the beginning of the project. Alphavantage (https://www.alphavantage.co/documentation/) is limited to 25 API requests per day, while Polygon (https://polygon.io/docs/stocks) is also limited to 5 API request per minute. You can find these test files in the tests folder. Yahoo Finance API has 2000 API requests per hour, so I decided to implement that in the information system. (https://algotrading101.com/learn/yfinance-guide/, https://pypi.org/project/yfinance/)

SQL code:

CREATE TABLE `users` (
  `userid` int NOT NULL AUTO_INCREMENT,
  `username` varchar(45) DEFAULT NULL,
  `email` varchar(45) DEFAULT NULL,
  `password` varchar(45) DEFAULT NULL,
  `full_name` varchar(45) DEFAULT NULL,
  `date_of_birth` datetime DEFAULT NULL,
  `phone_number` varchar(45) DEFAULT NULL,
  `address` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`userid`)
CREATE TABLE `user_portfolio` (
  `portfolio_id` int NOT NULL AUTO_INCREMENT,
  `ticker` varchar(45) NOT NULL,
  `userid` int NOT NULL,
  PRIMARY KEY (`portfolio_id`),
  KEY `userid_idx` (`userid`),
  CONSTRAINT `userid` FOREIGN KEY (`userid`) REFERENCES `users` (`userid`)
CREATE TABLE `transactions` (
  `transaction_id` int NOT NULL AUTO_INCREMENT,
  `ticker` varchar(45) NOT NULL,
  `purchase_date` datetime NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `userid` int NOT NULL,
  PRIMARY KEY (`transaction_id`),
  KEY `userid_tr_idx` (`userid`),
  CONSTRAINT `userid_tr` FOREIGN KEY (`userid`) REFERENCES `users` (`userid`)