<!DOCTYPE html>
<html>
  <head>
    <title>Bootstrap 101 Template</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Bootstrap -->
    <link href="css/bootstrap.min.css" rel="stylesheet" media="screen">
    <link href="css/styles.css" rel="stylesheet" media="screen">

    <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/libs/html5shiv/3.7.0/html5shiv.js"></script>
      <script src="https://oss.maxcdn.com/libs/respond.js/1.3.0/respond.min.js"></script>
    <![endif]-->
  </head>
  <body>
    <div class="container">
      <div class="row">

        <div class="col-md-4">
          <div class="iphone">
          <div id="carousel-example-generic" class="carousel slide" data-ride="carousel">
            <!-- Indicators -->

            <!-- Wrapper for slides -->
            <div class="carousel-inner">
              <div class="item active">
                <img src="img/screen-1.png">
              </div>

              <div class="item">
                <img src="img/screen-2.png">
              </div>

              <div class="item">
                <img src="img/screen-3.png">
              </div>

              <div class="item">
                <img src="img/screen-4.png">
              </div>

              <div class="item">
                <img src="img/screen-5.png">
              </div>

              <div class="item">
                <img src="img/screen-6.png">
              </div>

            </div>

            <!-- Controls -->
            <a class="left carousel-control" href="#carousel-example-generic" data-slide="prev">
              <span class="glyphicon glyphicon-chevron-left"></span>
            </a>
            <a class="right carousel-control" href="#carousel-example-generic" data-slide="next">
              <span class="glyphicon glyphicon-chevron-right"></span>
            </a>
          </div>
          </div>
        </div><!-- /end md-col-3 -->

        <div class="col-md-8">
          <div class="col-md-6">
            <ul class="list-inline">
              <li><a href="https://twitter.com/Menuflick">Twitter</a></li>
              <li><a href="https://www.facebook.com/menuflick">Facebook</a></li>
              <li><a href="http://www.menuflick.com/learn-more">Learn More</a></li>
            </ul>
          </div><!-- /end .col-md-2 -->
          <img src="img/logo.png" class="logo">
          <h1>See & Vote for the best Restaurant Dishes, Anywhere.</h1>
          <a href="#"><img src="img/app-store-logo.png"></img>

        </div><!-- /end .md-col-9 -->

      </div><!-- /end .row -->
    </div><!-- /end .container -->

    <footer>
      <div class="container">
          <div class="col-md-5 col-md-offset-4">
            <h2 class="pull-right">Subscribe to Our Mailing List for Updates:</h2>
          </div><!-- /end .col-md-8 -->
            <form>
              <div class="col-md-3">
                <input type="email" placeholder="Email Address" class="form-control pull-left">
                <button type="submit" class="btn btn-default pull-right">Submit</button>
              </div>
            </form> 
          </div><!-- /end .col-md-4 -->
        </div><!-- /end .row -->
      </div><!-- /end .container -->
    </footer>

    <script>

      var _gaq = _gaq || [];
      _gaq.push(['_setAccount', 'UA-39574765-1']);
      _gaq.push(['_trackPageview']);

      (function() {
        var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
        ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
      })();

    </script>
    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="https://code.jquery.com/jquery.js"></script>
    <!-- Include all compiled plugins (below), or include individual files as needed -->
    <script src="js/bootstrap.min.js"></script>
  </body>
</html>
