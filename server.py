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

    global clients_online
    clients_online -= 1

@sio.on('my_ping')
def my_ping(sid):
    sio.emit('my_pong', room=sid)

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
            clients[sid]['logged_in'] = True
            clients[sid]['uid'] = res['id']

            users[res['id']] = {
                'username': res['username'],
                'online': True
            }

            sio.emit('logged_in', details['username'], room=sid)

        else:
            # Don't specify that the password is just incorrect, otherwise
            # malicious actors could farm for usernames
            sio.emit('invalid_credentials', room=sid)

    else:
        sio.emit('invalid_credentials', room=sid)

#* Game Setup
@sio.on('create_lobby')
def create_lobby(sid):
    uid = clients[sid]['uid']

    if uid not in users:
        return # TODO: Log this event

    lobbies[uid] = {
        'players': [ users[uid]['username'] ]
    }

    sio.emit('lobby_data', lobbies[uid], room=sid)

@sio.on('get_open_lobbies')
def get_open_lobbies(sid):
    sio.emit('open_lobbies', lobbies, room=sid)


#*################################################################### ENTRY
if __name__ == '__main__':
    main()
