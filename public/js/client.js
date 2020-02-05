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

        else if (e.target.id == 'navbar-create-lobby') {
            $('#lobby').show();
            socket.emit('create_lobby');
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
    let ping_sent = 0;

    setInterval(() => {
        ping_sent = new Date().getTime();
        socket.emit('my_ping');
    }, 3000);

    socket.on('my_pong', () => {
        const delay = new Date().getTime() - ping_sent;
        $('#navbar-status').html(delay.toString() + 'ms');
    })

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

    socket.on('logged_in', (username) => {
        alert('Logged in');
        $('#login').hide();

        $('#navbar-account').html('Logged in as ' + username);
        $('#navbar-login-required').show();
    });

    //* Game Setup
    socket.on('lobby_data', (data) => {
        $('#lobby-info').html('<p>' + JSON.stringify(data) + '</p>');
    });
});
