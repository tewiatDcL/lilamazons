import eventlet
import socketio

static_files = {
    '/': 'pages/index.html'
}

def main():
    global static_files

    sio = socketio.Server()
    app = socketio.WSGIApp(sio, static_files=static_files)
    eventlet.wsgi.server(eventlet.listen(('', 8000)), app)

if __name__ == '__main__':
    main()
