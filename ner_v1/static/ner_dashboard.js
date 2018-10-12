$(document).ready(function(){

    $("#typedropdown li a").click(function(event){       	    	
		 $(this).parent().parent().siblings(".btn:first-child").html($(this).text()+' <span class="caret"></span>');
		 var entitytype = $(this).text();
		 if (entitytype == "Text"){	
			$("#entitynamefield").show();		 		 
		 	$("#entitynamefield").empty().html("<button class=\"btn btn-default dropdown-toggle\" type=\"button\" id=\"entitynames\" data-toggle=\"dropdown\" aria-haspopup=\"true\" aria-expanded=\"true\">Entity Name<span class=\"caret\"></span></button><ul class=\"dropdown-menu\" aria-labelledby=\"entitytypes\"><li><a href=\"#\">Brand</a></li><li><a href=\"#\">Clothes</a></li><li><a href=\"#\">Cuisine</a></li><li><a href=\"#\">Dish</a></li><li><a href=\"#\">Footwear</a></li><li><a href=\"#\">Movie</a></li><li><a href=\"#\">Restaurant</a></li></ul>");
		 	$("#entitynamefield li a").click(function(event){       	    	
		 		$(this).parent().parent().siblings(".btn:first-child").html($(this).text()+' <span class="caret"></span>');
			});
		 }
		 else{
		 	$("#entitynamefield").show();
		 	$("#entitynamefield").empty().html("<div class=\"input-group input-group-lg\"> <input type=\"text\" class=\"form-control\" placeholder=\"Entity Name\" id=\"entitynameinput\"></div>")
		 }

    });



    $("#entitysubmitbtn").click(function(){
    	var entityType = $("#entitytypes").text();
   		var entityName = $("#entitynames").text();
   		if (!entityName){
   			entityName = $("#entitynameinput").val();
   		}
   		var structuredValue = $("#structuredvalue").val();
   		var botMessage = $("#botmessage").val();
   		var message = $("#message").val();
   		var fallbackValue = $("#fallbackvalue").val();

   		var entityUrl = "/v1/" + entityType.trim().toLowerCase().replace(/ /g,"_") + "/";

   		$.ajax({
   			url: entityUrl,
   			type: "get",
            contentType:"application/json",
   			data: {
   				message: message.trim(),
   				entity_name: entityName.trim().toLowerCase(),
   				structured_value: structuredValue.trim(),
   				bot_message: botMessage.trim(),
   				fallback_value: fallbackValue.trim(),

   			},
   			success: function(data, textStatus, XmlHttpRequest){
                var str = JSON.stringify(data, undefined, 4);
                output(syntaxHighlight(str));
   			},
   			error: function(xhr, a, b){
   				var errorMessage = 'Oops! Something went wonrg, please check your input data';
   				output(errorMessage);
   			}

   		});
   		
    });

	var obj = {a:1, 'b':'foo', c:[false,'false',null, 'null', {d:{e:1.3e5,f:'1.3e5'}}]};
	var str = JSON.stringify(obj, undefined, 4);

});

function output(inp) {
    $("#entityoutput").html(inp);
}

/*
 Function to sytax highlight the JSON. Gotten by stack overflow answer 
 https://stackoverflow.com/questions/4810841/how-can-i-pretty-print-json-using-javascript
*/
function syntaxHighlight(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'key';
            } else {
                cls = 'string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'boolean';
        } else if (/null/.test(match)) {
            cls = 'null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}
