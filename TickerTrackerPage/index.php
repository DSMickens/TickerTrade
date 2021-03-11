<!DOCTYPE html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="style.css">
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ78Ω4/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">

    <title>TCKRTracker</title>
  </head>
  <header>
  <!-- navbar -->
    <div class="container">
      <div class="row">
        <nav class="navbar navbar-expand-lg ">
          <a class="navbar-brand" href="#">Home</a>
          <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse " id="navbarSupportedContent">
            <ul class="navbar-nav mr-4">
              <li class="nav-item">
                <a class="nav-link" data-value="tickers" href="./tickers.php">Tickers</a> </li>
            </ul>
          </div>
        </nav>
      </div>
  </header>
  <body>
    <div class="container">
      <div class="row">
        <!-- https://www.w3schools.com/php/func_mysqli_connect.asp -->
        <?php
            include 'passwords.php';
            // Create connection
            $conn = new mysqli($servername, $username, $password, $dbname);
            // Check connection
            if ($conn->connect_error) {
              die("Connection failed: " . $conn->connect_error);
            }

            $query = "SELECT id, ticker, open_time FROM trades";
            $response = $conn->query($query);

            if ($response->num_rows > 0): ?>
              <table class = "sortable table"><tr><th>ID</th><th>TICKER</th><th>OPEN TIME</th></tr>
              <?php while($row = $response->fetch_assoc()): ?>
                <tr><td><?php echo $row["id"]; ?></td><td> <?php echo $row["ticker"]; ?></td><td><?php echo $row["open_time"]; ?></td></tr>
              <?php endwhile ?>
              </table>
            <?php else:
              echo "0 results";

            $conn->close();
            endif;
            ?>
      </div>
    </div>
    <div class="container">
      <div class = "row">
        <img id="pl_chart", src="http://localhost/~Danny/TickerTrackerPage/images/daily_pl.png", alt>
        <p>234</p>
      </div>
    </div>
    <!-- Optional JavaScript -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
  </body>
</html>
