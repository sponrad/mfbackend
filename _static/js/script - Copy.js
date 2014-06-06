(function(jQuery) {
  $('a[href*=#]:not([href=#])').click(function() {
    if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
      var target = $(this.hash);
      target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
      if (target.length) {
        $('html,body').animate({
          scrollTop: target.offset().top
        }, 1000);
        return false;
      }
    }
  });
  window.mySwipe = Swipe(document.getElementById('slider'));

  $('[href="#top"]').hide();

  var step1 = $('#step-1').offset().top,
      step2 = $('#step-2').offset().top,
      step3 = $('#step-3').offset().top,
      top = $('#top').offset().top,
      $window = $(window);

  console.log(step3);
  $window.scroll(function() {
    console.log($window.scrollTop());
  });

  $window.scroll(function() {
      if ( $window.scrollTop() >= step1 ) {
        $('[href="#top"]').fadeIn();
        $('.down-arrow').attr('href', '#step-2');
        $('.up-arrow').attr('href', '#top');
      }
      if ( $window.scrollTop() <= step1 - 10 ) {
        $('[href="#top"]').fadeOut();
      }
      if ( $window.scrollTop() >= step2 - 10 ) {
        $('.up-arrow').attr('href', '#step-1');
        $('.down-arrow').attr('href', '#step-3');
      }
      if ( $window.scrollTop() >= step3 ) {
        $('.up-arrow').attr('href', '#step-2');
        $('.down-arrow').fadeOut();
      }
      if ($window.scrollTop() === top) {
        $('[href="#top"]').fadeOut();
        $('.down-arrow').attr('href', '#step-1');
      }
  });
})($);
