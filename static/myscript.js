
$(document).ready(function() {
    // Connect to the Socket.IO server.
    // The connection URL has the following format, relative to the current page:
    //     http[s]://<domain>:<port>[/<namespace>]
    var socket = io();

    // Event handler for new connections.
    // The callback function is invoked when a connection with the
    // server is established.
    socket.on('connect', function() {
        socket.emit('my_event', {data: 'I\'m connected!'});
    });

    

    // Test response received from server is handled here
    socket.on('test_response', function(msg) {
        $('#log').prepend('<br>' + $('<div/>').text(msg.data).html());
    })
    socket.on('enable_btn', function(msg) {
        $('#log').prepend('<br>' + $('<div/>').text(msg.data).html());
        document.getElementById('btn').disabled = false;
    })


    // Handlers for the different forms in the page.
    // These accept data from the user and send it to the server in a
    // variety of ways
    $('form#test').submit(function(event) {
        document.getElementById('btn').disabled = true;
        const cb = document.querySelector('#accept');
        console.log(cb.checked);


        if (cb.checked == true) {
            var prefixField = document.getElementById('appre').value;
            var outputText ="";
            
            var intAntalField = parseInt(document.getElementById('antap').value,10);
            var intStartField = parseInt(document.getElementById('apstart').value,10);
            var totalAP = intAntalField + intStartField;
            

            //Padding for output, eg. 1 becomes 001 and 20 becomes 020 
            function lpad(value, padding) {
                var zeroes = new Array(padding+1).join("0");
                return (zeroes + value).slice(-padding);
                }

            do {
                outputText += prefixField + lpad(intStartField,3) + ",";
                outputText += "\n";
                intStartField++;
                }
            while (intStartField < totalAP);   

            const csv = outputText.replace(/,\s*$/, ""); //Delete last comma.. 
            //console.log(csv);
            var hiddenElement = document.createElement('a');
            hiddenElement.href = 'data:text/csv;charset=utf-8,' + encodeURI(csv);
            hiddenElement.target = '_blank';
            hiddenElement.download = 'etikett.csv';
            hiddenElement.click();
        }

        
        //Uncomment for Flask to get message and begin processing.
        //socket.emit('test_message', {data: 'Here comes the configs for the AP:s'});
        //socket.emit('test_message', {appre: $('#appre').val(), antap: $('#antap').val(),apstart: $('#apstart').val(), aploc: $('#aploc').val()});
        
        return false;
    });
});

