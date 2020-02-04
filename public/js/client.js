const socket = io();

$(() => {
    console.log('Page loaded');


    //*************************************************************** GUI
    $('#navbar').on('click', 'a', (e) => {
        if (e.target.id == 'navbar-register') {
            if ($('#register').is(':visible')) {
                $('#register').hide();
            } else {
                $('#register').show();
            }
        }
    });

    $('#register').on('click', 'input', (e) => {
        if (e.target.id == 'btn-register') {
            socket.emit('register', {
                username: $('#register-username').val(),
                password: $('#register-password').val()
            });
        }
    });


    //*************************************************************** SERVER COMMS
    socket.on('username_taken', () => {
        alert('Username taken');
    });

    socket.on('registered', () => {
        alert('Registered');
        $('#register').hide();
    });
});
