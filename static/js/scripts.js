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
    }, 60000);
}

// Index page
$(document).ready(function () {             
    tickers.forEach(function (ticker) {
        addTickerToGrid(ticker);        
    });
    updatePrices();                         // Call updatePrices
    startUpdateCycle();                     // Call price update every 60s

    $('#add-ticker-form').submit(function (e) {
        e.preventDefault();
        var newTicker = $('#new-ticker').val().toUpperCase();
        if (!tickers.includes(newTicker)) {
            tickers.push(newTicker);
            localStorage.setItem('tickers', JSON.stringify(tickers));
            addTickerToGrid(newTicker);            
        }
        $('#new-ticker').val('');
        updatePrices();
    });
});

// Portfolio page
$(document).ready(function () {             
    fetch('/tickers')
        .then(response => response.json())
        .then(data => data['tickers'])
        .then(tickers => {
            tickers.forEach(function (ticker) {
                addLiveTicker1(ticker);        
            });
        });
    updatePrices();                         
    startUpdateCycle();                     

    $('#add-ticker-form2').submit(function (e) {
        e.preventDefault();
        var newTicker2 = $('#new-ticker2').val().toUpperCase();
        addLiveTicker(newTicker2);
        $('#new-ticker2').val('');
        updatePrices();
    });

    let addLiveTicker = (newTicker2) => {                  
        if (!tickers.includes(newTicker2)) {
            tickers.push(newTicker2);
            fetch('/portfolio', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ticker: newTicker2 })
            })
            .then(response => response.json())
            .then(data => {})
            .catch(() => alert("Test alert"));                               
            localStorage.setItem('tickers', JSON.stringify(tickers));
            addTickerToGrid2(newTicker2);            
        }
    };

    let addLiveTicker1 = (newTicker2) => {
        if (!tickers.includes(newTicker2)) {
            tickers.push(newTicker2);
            localStorage.setItem('tickers', JSON.stringify(tickers));
            addTickerToGrid2(newTicker2);
            updatePrices();
        }
    };

    $('#tickers-grid2').on('click', '.remove-btn', function () {         
        var tickerToRemove = $(this).data('ticker');                    
        tickers = tickers.filter(t => t !== tickerToRemove);              
        
        fetch('/remove_ticker', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ticker: tickerToRemove })
        })
        .then(response => response.json())
        .then(data => {
            if (data.result === 'success') {
                localStorage.setItem('tickers', JSON.stringify(tickers));
                $(`#${tickerToRemove}`).remove();
            } else {
                alert('Failed to remove ticker');
            }
        })
        .catch(() => alert('Failed to remove ticker'));
    });
});

// Index page grid
function addTickerToGrid(ticker) {
    $('#tickers-grid').append(`<div id="${ticker}" class="stock-box"><h2>${ticker}</h2><p id="${ticker}-price"></p><p id="${ticker}-pct"></p></div>`);
}                                                           // Function adds ticker box to html grid. ID, name, placeholder for price and % change

// Portfolio page grid
function addTickerToGrid2(ticker) {
    $('#tickers-grid2').append(`<div id="${ticker}" class="stock-box"><h2>${ticker}</h2><p id="${ticker}-price"></p><p id="${ticker}-pct"></p><button class="remove-btn" data-ticker="${ticker}">Remove</button></div>`);
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
                    colorClass = 'dark-red';
                } else if (changePercent < 0) {
                    colorClass = 'red';
                } else if (changePercent === 0) {
                    colorClass = 'gray';
                } else if (changePercent <= 2) {
                    colorClass = 'green';
                } else {
                    colorClass = 'dark-green';
                }

                $(`#${ticker}-price`).text(`$${data.currentPrice.toFixed(2)}`);
                $(`#${ticker}-pct`).text(`${changePercent.toFixed(2)}%`);
                $(`#${ticker}-price`).removeClass('dark-red gray green dark-green').addClass(colorClass);
                $(`#${ticker}-pct`).removeClass('dark-red gray green dark-green').addClass(colorClass);
            }
        });
    });
}
// reference: NeuralNine - Real-Time Stock Price Tracker in Python https://youtu.be/GSHFzqqPq5U?list=PLF6w5cpj_zBo6dTD4avNwz1xbqYRiKBsN

// Function to add a new transaction
$('#add-transaction-form').submit(function (e) {
    e.preventDefault();
    var ticker = $('#ticker').val().toUpperCase();  
    var purchaseDate = $('#purchase-date').val();
    var amount = $('#amount').val();

    fetch('/add_transaction', {                     
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ticker: ticker, purchase_date: purchaseDate, amount: amount })
    })
    .then(response => response.json())                      
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
function addTransactionToTable(ticker, purchaseDate, amount, investedValue, totalValue, profitLoss) {
    if ($(`#transaction-list tr:contains(${ticker}):contains(${purchaseDate})`).length === 0) {
        $('#transaction-list').append(`
            <tr>
                <td>${ticker}</td>
                <td>${purchaseDate}</td>
                <td>${amount}</td>
                <td>${investedValue.toFixed(2)}</td>
                <td>${totalValue.toFixed(2)}</td>
                <td>
                    ${profitLoss >= 0 ? `<span class="text-success">${profitLoss.toFixed(2)}</span>` : `<span class="text-danger">${profitLoss.toFixed(2)}</span>`}
                </td>
                <td><button class="btn btn-danger btn-sm remove-transaction-btn">Remove</button></td>
            </tr>
        `);
    }
}

// Fetch and display transactions on page load
$(document).ready(function () {
    $('#transaction-list').empty(); // Clear the transaction list before appending new transactions to avoid duplication

    let totalInvestedValue = 0;
    let totalPortfolioValue = 0;

    fetch('/get_transactions')
        .then(response => response.json())
        .then(transactions => {
            let promises = transactions.map(transaction => {
                return $.ajax({
                    url: '/get_stock_data',
                    type: 'POST',
                    data: JSON.stringify({ 'ticker': transaction.ticker }),
                    contentType: 'application/json; charset=utf-8',
                    dataType: 'json'
                }).then(data => {
                    let purchaseDate = transaction.purchase_date;
                    let amount = transaction.amount;

                    // Fetch historical price for the purchase date
                    return $.ajax({
                        url: '/get_historical_price',
                        type: 'POST',
                        data: JSON.stringify({ 'ticker': transaction.ticker, 'purchase_date': purchaseDate }),
                        contentType: 'application/json; charset=utf-8',
                        dataType: 'json'
                    }).then(priceData => {
                        let investedValue = amount * priceData.unitPrice;
                        let totalValue = amount * data.currentPrice;
                        let profitLoss = totalValue - investedValue;

                        // Add to the overall totals
                        totalInvestedValue += investedValue;
                        totalPortfolioValue += totalValue;

                        // Add transaction row to the table
                        addTransactionToTable(transaction.ticker, purchaseDate, amount, investedValue, totalValue, profitLoss);
                    });
                });
            });

            // After all promises resolve, update the portfolio and invested totals
            Promise.all(promises).then(() => {
                $('#portfolio-total').text(`$${totalPortfolioValue.toFixed(2)}`);
                $('#portfolio-invested').text(`$${totalInvestedValue.toFixed(2)}`);

                // Call to update the portfolio value chart
                updatePortfolioChart(transactions);
            });
        });
});

// Handle remove transaction button click
$(document).on('click', '.remove-transaction-btn', function () {
    var row = $(this).closest('tr');
    var ticker = row.find('td:nth-child(1)').text();
    var purchaseDate = row.find('td:nth-child(2)').text();

    // Ask for confirmation before removing the transaction
    if (confirm('Are you sure you want to remove this transaction?')) {
        fetch('/remove_transaction', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'ticker': ticker, 'purchase_date': purchaseDate })
        })
        .then(response => response.json())
        .then(data => {
            if (data.result === 'success') {
                row.remove();
            } else {
                alert('Failed to remove transaction');
            }
        })
        .catch(() => alert('Failed to remove transaction'));
    }
});

// Total investment over time Chart.js
function updatePortfolioChart(transactions) {
    const ctx = document.getElementById('portfolio-chart').getContext('2d');
    let labels = [];
    let portfolioValues = [];
    let cumulativePortfolioValue = 0; // Track the portfolio value over time

                                        // Fetch current data for each transaction (stock)
    let promises = transactions.map(transaction => {
        return $.ajax({
            url: '/get_stock_data',  // Use the current price for the portfolio value calculation
            type: 'POST',
            data: JSON.stringify({ 'ticker': transaction.ticker }),
            contentType: 'application/json; charset=utf-8',
            dataType: 'json'
        }).then(data => {
            let currentPrice = data.currentPrice;
            let amount = transaction.amount;
            let totalValue = amount * currentPrice; // Calculate the value based on current price
            let currentDate = new Date(transaction.purchase_date).toISOString().split('T')[0];

            return { date: currentDate, value: totalValue };
        });
    });

                            // After all promises resolve, update the chart
    Promise.all(promises).then(results => {
                            // Sort results by date in ascending order
        results.sort((a, b) => new Date(a.date) - new Date(b.date));

                                // Add sorted data to labels and values, and calculate cumulative portfolio value
        results.forEach(result => {
            labels.push(result.date);
            cumulativePortfolioValue += result.value;                       // Accumulate the portfolio value over time
            portfolioValues.push(cumulativePortfolioValue);                 // Push the cumulative value
        });

        // Create the chart
        const portfolioChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Portfolio Value',
                    data: portfolioValues,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    fill: false
                }]
            },
            options: {
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Portfolio Value ($)'
                        }
                    }
                }
            }
        });
    });
}
