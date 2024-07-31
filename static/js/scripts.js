
window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

});





var tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'INTC', 'PLTR', 'WCBR', 'SPY', 'ETH-USD', 'BTC-USD']; // List of popular stocks

function startUpdateCycle() {
    updatePrices();
    setInterval(function () {
        updatePrices(); // Update prices every minute
    }, 60000)
}

$(document).ready(function () {
    tickers.forEach(function (ticker) {
        addTickerToGrid(ticker);
    });

    updatePrices();

    startUpdateCycle();

    $('#add-ticker-form').submit(function (e) {
        e.preventDefault();
        var newTicker = $('#new-ticker').val().toUpperCase();
        if (!tickers.includes(newTicker)) {
            tickers.push(newTicker);
            addTickerToGrid(newTicker);
        }
        $('#new-ticker').val('');
        updatePrices();
    });
});

function addTickerToGrid(ticker) {
    $('#tickers-grid').append(`<div id="${ticker}" class="stock-box"><h2>${ticker}</h2><p id="${ticker}-price"></p><p id="${ticker}-pct"></p></div>`)
}

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
