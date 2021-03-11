function display_ticker_chart(ticker, day) {
  const image = ticker + "_img";
  const date = day.split(' ')[0];
  const image_url = "http://localhost/~Danny/TickerTrackerPage/images/charts/" + ticker + "/" + date + ".png";
  $.ajax({
    url: image_url,
    type: 'HEAD',
    success: function(data) {
      doc = document.getElementById(image);
      doc.src=image_url;
      doc.height=350;
      doc.width=450;
      doc.style.visibility="visible";
    },
    error: function(data) {
      alert("This chart is currently unavailable. Please wait one moment while we generate the graph.");
      $.ajax({
        type: 'POST',
        url: "http://localhost/~Danny/TickerTrackerPage/scripts/python/frontEndSupport.py",
        data: {function: "ticker graph",
               ticker: ticker,
               day: day},
        dataType: "text",
        success: function(response){
          doc = document.getElementById(image);
          doc.src=image_url;
          doc.height=350;
          doc.width=450;
        },
        error: function(data) {
          alert("There was a problem creating the requested graph.")
          console.log(data);
        }
      });
    }
  });
}

function hide_ticker_chart(ticker) {
  const image = ticker + "_img";
  doc = document.getElementById(image);
  doc.style.visibility="hidden";
}

function display_pl_chart() {

}
