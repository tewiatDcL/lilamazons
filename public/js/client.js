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

        else if (e.target.id == 'navbar-browse-games') {
            $('#game-browser').show();
            socket.emit('get_open_lobbies');
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

    //* Game Browser
    $('#lobbies-list').on('click', 'a', (e) => {
        socket.emit('join_lobby', e.target.id);
    });

    //* Lobby
    $('#lobby').on('click', 'input', (e) => {
        if (e.target.id == 'btn-lobby-start') {
            socket.emit('lobby_start');
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
        $('#status-ping').html(delay.toString() + 'ms');
        $('#status-ping').removeClass('error');
    })

    socket.on('disconnect', () => {
        $('#status-ping').html('DISCONNECTED');
        $('#status-ping').addClass('error');
    });

    setInterval(() => {
        socket.emit('get_server_stats');
    }, 10000);

    socket.on('server_stats', (stats) => {
        const users   = 'Logged in ' + stats.users_online.toString();
        const clients = stats.clients_online.toString() + ' online';
        $('#status-online').html(users + '/' + clients);
    });

    //* Account
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
        $('#lobby').show();
        $('#lobby-info').html('<p>' + JSON.stringify(data) + '</p>');
    });

    socket.on('open_lobbies', (lobbies) => {
        let html = '<table><tr><td><p>Lobby ID</p></td><td><p>Players</p></td><td><p>Join</p></td></tr>';

        for (let k in lobbies) {
            let players = '';
            for (p in lobbies[k].players) {
                players += p + ', ';
            }

            html += '<tr><td><p>'
                + lobbies[k].id.toString()
                + '</p></td><td><p>'
                + players.slice(0, -2)
                + '</p></td><td><p><a href="#" id="'
                + lobbies[k].id.toString()
                + '">Join</a></p></td>';
        }

        html += '</table>'
        $('#lobbies-list').html(html);
    });
});
