import os

import eventlet
import socketio


#*################################################################### SETUP
sio = socketio.Server()

static_files = {
    '/': 'pages/index.html',
    '/js/client': 'public/js/client.js',
    '/css/default': 'public/css/default.css'
}


#*################################################################### MAIN
def main():
    global sio
    global static_files

    app = socketio.WSGIApp(sio, static_files=static_files)

    port = 8000
    if 'PORT' in os.environ:
        port = os.environ['PORT']

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
    print(f'Registration: {details["username"]}')


#*################################################################### ENTRY
if __name__ == '__main__':
    main()
