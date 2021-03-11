<!DOCTYPE html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    <link rel="stylesheet" href="./css/style.css">
    <title>TCKRTracker</title>
  </head>
  <!-- navbar -->
  <header>
    <nav class="navbar navbar-expand-lg ">
      <a class="navbar-brand" href="./index.php">Home</a>
      <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
    </nav>
  </header>
  <body>
    <div class="container">
      <?php
        include 'passwords.php';
        // Create connection
        $conn = new mysqli($servername, $username, $password, $dbname);
        // Check connection
        if ($conn->connect_error) {
          die("Connection failed: " . $conn->connect_error);
        }

        $query = "SELECT DISTINCT ticker FROM trades";
        $response = $conn->query($query);

        if ($response->num_rows > 0):
          while ($row = $response->fetch_assoc()):?>
            <div class="row">
            <div class="col-9">
            <h2><?php echo $row["ticker"]; ?></h2>
            <?php
            $query2 = "SELECT success, p_l, position_closure_reason, open_time, dia_at_open, spy_at_open, qqq_at_open FROM trades ";
            $query2 .= "WHERE ticker = \"".$row["ticker"]."\"";
            $response2 = $conn->query($query2);
            if ($response2->num_rows > 0):?>
              <div class="table-responsive">
              <table class="table table-striped table-bordered table-sm" cellspacing="0"width="100%">
                <thead><tr><th>SUCCESS</th><th>P/L</th><th>CLOSURE REASON</th><th>DIA</th><th>SPY</th><th>QQQ</th><th>CHART</th></tr></thead>
              <!--output data of each row-->
              <tbody>
            <?php
              while($row2 = $response2->fetch_assoc()):?>
                <tr><td><?php echo $row2["success"] ? 'True' : 'False'; ?></td>
                <td><?php echo $row2["p_l"]; ?></td>
                <td><?php echo $row2["position_closure_reason"]; ?></td>
                <td><?php echo $row2["dia_at_open"]; ?></td>
                <td><?php echo $row2["spy_at_open"]; ?></td>
                <td><?php echo $row2["qqq_at_open"]; ?></td>
                <td><button onclick="display_ticker_chart(<?php echo "'".$row["ticker"]."'".",'".$row2["open_time"]."'";?>)">Display Chart</button>
                    <button onclick="hide_ticker_hart(<?php echo "'".$row["ticker"]."'";?>)">Hide Chart</button></td></tr>
              <?php endwhile;?>
              </tbody>
            </table>
          </div>
            <?php endif; ?>
            </div>
            <div class="col-3">
            <img id="<?php echo $row["ticker"]."_img";?>"src="data:," alt>
            </div>
            </div>
          <?php endwhile;?>
        <?php endif;
        $conn->close();
      ?>
      </div>
    </div>

    <!-- function displayChart -->
    <script src="http://localhost/~Danny/TickerTrackerPage/scripts/javascript/charts.js"></script>
    <script src="https://cdn.datatables.net/1.10.23/js/jquery.dataTables.min.js"></script>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
  </body>
</html>
