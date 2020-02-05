from Game import Match

import json
import os

import eventlet
import psycopg2
import psycopg2.extras
import socketio


#*################################################################### SETUP
sio = socketio.Server()

static_files = {
    '/': 'pages/index.html',
    '/js/client': 'public/js/client.js',
    '/css/default': 'public/css/default.css'
}

# PostgreSQL
if 'DATABASE_URL' in os.environ:
    db_url = os.environ['DATABASE_URL']
else:
    db_url = json.load(open('config.json', 'r'))['db_url']

con = psycopg2.connect(db_url)
cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print('Connected to DB') # TODO: Actually check for success

# Server operation
clients = {} # Those who are NOT logged in
users   = {} # Those who ARE logged in
clients_online = 0
users_online   = 0

lobbies = {}
lobby_id = 0

matches = {}


#*################################################################### MAIN
def main():
    global sio
    global static_files

    app = socketio.WSGIApp(sio, static_files=static_files)

    port = 8000
    if 'PORT' in os.environ:
        port = int(os.environ['PORT'])

    eventlet.wsgi.server(eventlet.listen(('', port)), app)


#*################################################################### SIO
@sio.on('connect')
def connect(sid, env):
    print(f'Connected: {sid}')

    clients[sid] = {
        'connected': True,
        'logged_in': False,
        'uid': None
    }

    global clients_online
    clients_online += 1

@sio.on('disconnect')
def disconnect(sid):
    print(f'Disconnected: {sid}')
    clients[sid]['connected'] = False

    uid = clients[sid]['uid']
    if uid:
        users[uid]['online'] = False

    global clients_online
    clients_online -= 1

    if clients[sid]['logged_in']:
        global users_online
        users_online -= 1

@sio.on('my_ping')
def my_ping(sid):
    sio.emit('my_pong', room=sid)

@sio.on('get_server_stats')
def get_server_stats(sid):
    # TODO: Change this to emit to all clients on server-based timing
    sio.emit('server_stats', {
        'clients_online': clients_online,
        'users_online': users_online
    }, room=sid)

#* Accounts
@sio.on('register')
def register(sid, details):
    # TODO: Perform validity checks. Store pw_hash. Store more info
    print(f'Registration: {details["username"]}')

    cur.execute(
        'SELECT count(*) FROM users WHERE username=%(username)s;',
        { 'username': details['username'] }
    )

    if cur.fetchone()[0]: # Username taken
        sio.emit('username_taken', room=sid)

    else:
        cur.execute("""
            INSERT INTO users (username, pw_hash)
            VALUES (%(username)s, %(pw_hash)s);
            """,
            {
                'username': details['username'],
                'pw_hash':  details['password']
            }
        )
        con.commit()

        sio.emit('registered', room=sid)

@sio.on('login')
def login(sid, details):
    print(f'Login from {details["username"]}')

    cur.execute(
        'SELECT * FROM users WHERE username=%(username)s;',
        { 'username': details['username'] }
    )

    res = cur.fetchone()
    if res: # User exists
        if res['pw_hash'] == details['password']:
            # Login succeeded
            # TODO: Disallow multiple logon?
            clients[sid]['logged_in'] = True
            clients[sid]['uid'] = res['id']

            if res['id'] not in users:
                users[res['id']] = {
                    'sid':      sid,
                    'username': res['username'],
                    'online':   True,
                    'in_lobby': None
                }
            else:
                users[res['id']]['sid']    = sid
                users[res['id']]['online'] = True

            sio.emit('logged_in', details['username'], room=sid)

            global users_online
            users_online += 1

            # Check whether the user had a lobby open
            in_lobby = users[res['id']]['in_lobby']

            if in_lobby:
                sio.emit('lobby_data', lobbies[in_lobby], room=sid)

        else:
            # Don't specify that the password is just incorrect, otherwise
            # malicious actors could farm for usernames
            sio.emit('invalid_credentials', room=sid)

    else:
        sio.emit('invalid_credentials', room=sid)

#* Game Setup
@sio.on('create_lobby')
def create_lobby(sid):
    # TODO: Lobbies should expire after a while
    uid = clients[sid]['uid']

    if uid not in users:
        return # TODO: Log this event

    # Make sure user isn't already in a lobby
    if users[uid]['in_lobby']:
        return # TODO: Present error message to user

    global lobby_id
    lid = lobby_id
    lobby_id += 1

    lobbies[lid] = {
        'id':      lid,
        'host_id': uid,
        'players': {
            users[uid]['username']: uid
        }
    }

    users[uid]['in_lobby'] = lid
    sio.emit('lobby_data', lobbies[lid], room=sid)

@sio.on('get_open_lobbies')
def get_open_lobbies(sid):
    sio.emit('open_lobbies', lobbies, room=sid)

@sio.on('join_lobby')
def join_lobby(sid, lobby_id):
    lobby_id = int(lobby_id)

    if lobby_id not in lobbies:
        # Lobby no longer exists
        return # TODO: Present error message to user

    uid = clients[sid]['uid']

    if uid not in users:
        return # TODO: Log this event

    # Make sure user isn't already in a lobby
    if users[uid]['in_lobby']:
        return # TODO: Present error message to user

    # Add current user to the lobby
    lobbies[lobby_id]['players'][users[uid]['username']] = uid
    users[uid]['in_lobby'] = lobby_id

    # Send the updated lobby data to all users in the lobby
    players = lobbies[lobby_id]['players']

    for p in players:
        usid = users[players[p]]['sid']
        sio.emit('lobby_data', lobbies[lobby_id], room=usid)

@sio.on('lobby_cancel')
def lobby_cancel(sid):
    uid = clients[sid]['uid']
    lobby_id = users[uid]['in_lobby']

    if lobby_id not in lobbies:
        return # TODO: Log this event

    if lobbies[lobby_id]['host_id'] == uid:
        # User is host, so kick everyone out of the lobby
        players = lobbies[lobby_id]['players']

        for p in players:
            uid  = players[p]
            usid = users[uid]['sid']

            users[uid]['in_lobby'] = None
            sio.emit('leave_lobby', room=usid)

        # Delete the lobby
        del lobbies[lobby_id]

    else:
        # User is just leaving a lobby themselves
        users[uid]['in_lobby'] = None
        sio.emit('leave_lobby', room=sid)

        del lobbies[lobby_id]['players'][users[uid]['username']]

        # Update the lobby for the remaining players
        players = lobbies[lobby_id]['players']

        for p in players:
            usid = users[players[p]]['sid']
            sio.emit('lobby_data', lobbies[lobby_id], room=usid)

@sio.on('lobby_start')
def lobby_start(sid):
    uid = clients[sid]['uid']
    lobby_id = users[uid]['in_lobby']

    if (lobby_id not in lobbies) or (uid != lobbies[lobby_id]['host_id']):
        return # TODO: Log this event

    matches[lobby_id] = Match.Match(lobby_id)


#*################################################################### ENTRY
if __name__ == '__main__':
    main()
