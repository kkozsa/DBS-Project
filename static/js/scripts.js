// Toggle the side navigation

window.addEventListener('DOMContentLoaded', event => {    
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {        
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }
});
// reference: Start Bootstrap - Simple Sidebar v6.0.6 (https://startbootstrap.com/template/simple-sidebar)
// Licensed under MIT (https://github.com/twbs/bootstrap/blob/main/LICENSE)



// Update prices every minute

function startUpdateCycle() {               
    updatePrices();
    setInterval(function () {
        updatePrices();                   
    }, 60000)
}


// Index page, 

$(document).ready(function () {             
    tickers.forEach(function (ticker) {
        addTickerToGrid(ticker);        
    });
    updatePrices();                         // Call updateprices
    startUpdateCycle();                     // Call price update 60s

    $('#add-ticker-form').submit(function (e) {
        e.preventDefault();
        var newTicker = $('#new-ticker').val().toUpperCase();
        if (!tickers.includes(newTicker)) {
            tickers.push(newTicker);
            localStorage.setItem('tickers', JSON.stringify(tickers))
            addTickerToGrid(newTicker);            
        }
        $('#new-ticker').val('');
        updatePrices();
    });
});


// Portfolio page

$(document).ready(function () {             // When document ready      
    fetch ('/tickers').then(data=>data.json())      
    .then(data=>data['tickers'])
    .then (tickers => tickers.forEach(function (ticker) {
        addLiveTicker1(ticker);        
    }));
    updatePrices();                         // Call updateprices
    startUpdateCycle();                     // Call price update 60s

    $('#add-ticker-form2').submit(
        function (e) {
        e.preventDefault();
        var newTicker2 = $('#new-ticker2').val().toUpperCase();
        addLiveTicker(newTicker2);

        
        $('#new-ticker2').val('');
        updatePrices();

    });

    let addLiveTicker=(newTicker2) =>{                  // Adding a new ticker, POST request to server to update portfolio
    if (!tickers.includes(newTicker2)) {
        tickers.push(newTicker2);
        fetch('/portfolio', {
            method: 'POST',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ticker: newTicker2})
          })
            .then (data => data.json())
            .then (data => {})
            .catch (_=> alert("Test alert"));                               
        localStorage.setItem('tickers', JSON.stringify(tickers))
        addTickerToGrid2(newTicker2);            
        }
    }

    let addLiveTicker1=(newTicker2) =>{
    if (!tickers.includes(newTicker2)) {
        tickers.push(newTicker2);
        localStorage.setItem('tickers', JSON.stringify(tickers))
        addTickerToGrid2(newTicker2);
        updatePrices();
    }}

    $('#tickers-grid2').on('click', '.remove-btn', function () {         // click event listener for elements with class remove-btn
        var tickerToRemove = $(this).data('ticker');                    // When a user clicks the "Remove" button associated with a ticker, this function executes.
        tickers=tickers.filter(t => t !== tickerToRemove);              
        
        fetch('/remove_ticker', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ticker: tickerToRemove })
        })
            .then(data => data.json())
            .then(data => {
                if (data.result === 'success') {
                    localStorage.setItem('tickers', JSON.stringify(tickers));
                    $(`#${tickerToRemove}`).remove();
                } else {
                    alert('Failed to remove ticker');
                }
            })
            .catch(_ => alert('Failed to remove ticker'));
    });
});


// Index page grid

function addTickerToGrid(ticker) {
    $('#tickers-grid').append(`<div id="${ticker}" class="stock-box"><h2>${ticker}</h2><p id="${ticker}-price"></p><p id="${ticker}-pct"></p></div>`)
}                                                           // Function adds ticker box to html grid. ID, name, placeholder for price and % change


// Portfolio page grid

function addTickerToGrid2(ticker) {
    $('#tickers-grid2').append(`<div id="${ticker}" class="stock-box"><h2>${ticker}</h2><p id="${ticker}-price"></p><p id="${ticker}-pct"></p><button class="remove-btn" data-ticker="${ticker}">Remove</button></div>`)
}                                                           // Same as above + remove button


// Send AJAX request to fetch stock data for tickers. Update price change

function updatePrices() {
    tickers.forEach(function (ticker) {
        $.ajax({
            url: '/get_stock_data',
            type: 'POST',
            data: JSON.stringify({ 'ticker': ticker }),
            contentType: 'application/json; charset=utf-8',
            dataType: 'json',
            success: function (data) {
                var changePercent = ((data.currentPrice - data.openPrice) / data.openPrice) * 100;
                var colorClass;
                if (changePercent <= -2) {
                    colorClass = 'dark-red'
                } else if (changePercent < 0) {
                    colorClass = 'red'
                } else if (changePercent == 0) {
                    colorClass = 'gray'
                } else if (changePercent <= 2) {
                    colorClass = 'green'
                } else {
                    colorClass = 'dark-green'
                }

                $(`#${ticker}-price`).text(`$${data.currentPrice.toFixed(2)}`);
                $(`#${ticker}-pct`).text(`$${changePercent.toFixed(2)}%`);
                $(`#${ticker}-price`).removeClass('dark-red graz green dark-green').addClass(colorClass);
                $(`#${ticker}-pct`).removeClass('dark-red graz green dark-green').addClass(colorClass);
            }
        })
    })
}
// reference: NeuralNine - Real-Time Stock Price Tracker in Python https://youtu.be/GSHFzqqPq5U?list=PLF6w5cpj_zBo6dTD4avNwz1xbqYRiKBsN

// Function to add a new transaction
$('#add-transaction-form').submit(function (e) {
    e.preventDefault();
    var ticker = $('#ticker').val().toUpperCase();  // Extracting data
    var purchaseDate = $('#purchase-date').val();
    var amount = $('#amount').val();

    fetch('/add_transaction', {                     // Sending data to server
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ticker: ticker, purchase_date: purchaseDate, amount: amount})
    })
    .then(data => data.json())                      // Server response
    .then(data => {
        if (data.result === 'success') {
            addTransactionToTable(ticker, purchaseDate, amount);
            $('#ticker').val('');
            $('#purchase-date').val('');
            $('#amount').val('');
        } else {
            alert('Failed to add transaction');
        }
    })
    .catch(() => alert('Failed to add transaction'));
});

// Function to add a transaction to the table
function addTransactionToTable(ticker, purchaseDate, amount, value) {
    $('#transaction-list').append(`
        <tr>
            <td>${ticker}</td>
            <td>${purchaseDate}</td>
            <td>${amount}</td>
            <td>${value.toFixed(2)}</td>
            <td><button class="btn btn-danger btn-sm remove-transaction-btn">Remove</button></td>
        </tr>
    `);
}

// Fetch and display transactions on page load
$(document).ready(function () {
    fetch('/get_transactions')
    .then(data => data.json())
    .then(transactions => {
        // Clear the transaction list before appending new transactions             AVOID DOUBLE DATA
        $('#transaction-list').empty();
        
        transactions.forEach(function (transaction) {
            addTransactionToTable(transaction.ticker, transaction.purchase_date, transaction.amount);
        });
    });
});


// Fetch and display transactions and total portfolio value on page load
$(document).ready(function () {
    // Fetch transactions
    fetch('/get_transactions')
        .then(response => response.json())
        .then(transactions => {
            $('#transaction-list').empty(); // Clear existing rows
            let totalPortfolioValue = 0;    // Initialize total value

            // Create a promise array for stock data fetches
            let promises = transactions.map(transaction => {
                return $.ajax({
                    url: '/get_stock_data',
                    type: 'POST',
                    data: JSON.stringify({ 'ticker': transaction.ticker }),
                    contentType: 'application/json; charset=utf-8',
                    dataType: 'json'
                }).then(data => {
                    var currentPrice = data.currentPrice;
                    var value = transaction.amount * currentPrice;
                    totalPortfolioValue += value;  // Add to total value

                    // Add transaction to table
                    addTransactionToTable(transaction.ticker, transaction.purchase_date, transaction.amount, value);
                });
            });

            // After all data is fetched and processed
            Promise.all(promises).then(() => {
                $('#portfolio-value').text(`$${totalPortfolioValue.toFixed(2)}`);
            });
        });
});
