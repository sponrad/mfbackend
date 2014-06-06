function convertRating(rating){
    switch(rating)
    {
    case 100:
	return "+"
	break;
    case 50:
	return "/"
	break;
    case 0:
	return "-"
	break;
    }
}

function parsePrompt(data){
    var html = "<div class='reviewItem'>";
    html += convertRating(data.rating) + " ";
    html += "<a class='profilelink' href='/profile?profileid="+data.userid+"'>" + data.username + "</a><br>";
    
    html += data.prompt
	.replace("{{input}}", "<span style='display: inline; color:red;'>"+data.input+"</span>")
	.replace("{{restaurant}}", "<a style='display: inline;' href='/items?restaurantid="+ data.restaurantid +"'>"+data.restaurant+"</a>")
	.replace("{{dish}}", "<a style='display: inline;' href='/vote?restaurantid="+data.restaurantid+"&itemid="+data.itemid+"&restaurantname="+data.restaurant+"&itemname="+data.item+"'>"+data.item+"</a>")
	.replace("{{input2}}", "<span type='text' name='input2' style='display: inline; color: red;'>"+data.input2+"</span>");

    html += "</div><br>";

    return html;
}

function utf8_decode(str_data) {
  //  discuss at: http://phpjs.org/functions/utf8_decode/
  // original by: Webtoolkit.info (http://www.webtoolkit.info/)
  //    input by: Aman Gupta
  //    input by: Brett Zamir (http://brett-zamir.me)
  // improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
  // improved by: Norman "zEh" Fuchs
  // bugfixed by: hitwork
  // bugfixed by: Onno Marsman
  // bugfixed by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
  // bugfixed by: kirilloid
  //   example 1: utf8_decode('Kevin van Zonneveld');
  //   returns 1: 'Kevin van Zonneveld'

  var tmp_arr = [],
    i = 0,
    ac = 0,
    c1 = 0,
    c2 = 0,
    c3 = 0,
    c4 = 0;

  str_data += '';

  while (i < str_data.length) {
    c1 = str_data.charCodeAt(i);
    if (c1 <= 191) {
      tmp_arr[ac++] = String.fromCharCode(c1);
      i++;
    } else if (c1 <= 223) {
      c2 = str_data.charCodeAt(i + 1);
      tmp_arr[ac++] = String.fromCharCode(((c1 & 31) << 6) | (c2 & 63));
      i += 2;
    } else if (c1 <= 239) {
      // http://en.wikipedia.org/wiki/UTF-8#Codepage_layout
      c2 = str_data.charCodeAt(i + 1);
      c3 = str_data.charCodeAt(i + 2);
      tmp_arr[ac++] = String.fromCharCode(((c1 & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
      i += 3;
    } else {
      c2 = str_data.charCodeAt(i + 1);
      c3 = str_data.charCodeAt(i + 2);
      c4 = str_data.charCodeAt(i + 3);
      c1 = ((c1 & 7) << 18) | ((c2 & 63) << 12) | ((c3 & 63) << 6) | (c4 & 63);
      c1 -= 0x10000;
      tmp_arr[ac++] = String.fromCharCode(0xD800 | ((c1 >> 10) & 0x3FF));
      tmp_arr[ac++] = String.fromCharCode(0xDC00 | (c1 & 0x3FF));
      i += 4;
    }
  }

  return tmp_arr.join('');
}

function parseVotePrompt(data, item, restaurant){
    //takes the prompt and returns an html string
    var html = "" + data.prompt;
    html = html.replace("{{input}}", "<input type='text' name='input' style='display: inline;'>");
    html = html.replace("{{input2}}", "<input type='text' name='input2' style='display: inline;'>");
    html = html.replace("{{restaurant}}", "<span style='color: red;'>"+utf8_decode(restaurant)+"</span>");
    html = html.replace("{{dish}}", "<span style='color: red;'>"+item+"</span>");
    html = html + "<input type='hidden' name='promptid' value='"+data.promptid+"'/>";

    return html;
}
