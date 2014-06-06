(function(jQuery) {
  $("#signupbutton").click( function(e){
    e.preventDefault();
    var formdata = $("#signupform").serialize();
    $.post('http://mfbackend.appspot.com/json/signup', formdata, function(returndata) {
      console.log(returndata);
      if (returndata.response === 1) {
        var signUpUsername = $('#signupform input[name="username"]').val();
        alert('Thanks for signing up, ' + signUpUsername + '! Please login on the next page.');
        window.location = 'http://menuflick.com';
      } else {
        alert("Something went wrong");
      }
    }, "json");
   });
})($);
