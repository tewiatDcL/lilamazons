const socket = io();

$(() => {
    console.log('Page loaded');


    //*************************************************************** GUI
    $('#navbar').on('click', 'a', (e) => {
        if (e.target.id == 'navbar-register') {
            if ($('#register').is(':visible')) {
                $('#register').hide();
            } else {
                $('#login').hide();
                $('#register').show();
            }
        }

        else if (e.target.id == 'navbar-login') {
            if ($('#login').is(':visible')) {
                $('#login').hide();
            } else {
                $('#register').hide();
                $('#login').show();
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

    $('#login').on('click', 'input', (e) => {
        if (e.target.id == 'btn-login') {
            socket.emit('login', {
                username: $('#login-username').val(),
                password: $('#login-password').val()
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

    socket.on('invalid_credentials', () => {
        alert('Invalid credentials');
    });

    socket.on('logged_in', () => {
        alert('Logged in');
        $('#login').hide();
    });
});
