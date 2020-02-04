import json
import os

import eventlet
import psycopg2
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
cur = con.cursor()

print('Connected to DB') # TODO: Actually check for success


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

@sio.on('disconnect')
def disconnect(sid):
    print(f'Disconnected: {sid}')

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


#*################################################################### ENTRY
if __name__ == '__main__':
    main()
