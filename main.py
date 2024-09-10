import http.server
import socketserver
import socket
import threading
import json
import os
from urllib.parse import parse_qs
from datetime import datetime

# Налаштування портів
HTTP_PORT = 3000
SOCKET_PORT = 5000
DATA_FILE = 'storage/data.json'

# HTTP сервер
class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Перевіряємо, чи існує файл
        if self.path == '/':
            self.path = '/templates/index.html'
        elif self.path == '/message.html':
            self.path = '/templates/message.html'
        elif self.path.startswith('/static/'):
            self.path = self.path[1:]  # Видаляємо початковий слеш
            return super().do_GET()
        else:
            self.path = '/templates/error.html'
            self.send_response(404)
            self.end_headers()
            with open('templates/error.html', 'rb') as file:
                self.wfile.write(file.read())
            return

        # Якщо файл знайдений
        return super().do_GET()

    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            params = parse_qs(body.decode('utf-8'))

            username = params.get('username', [''])[0]
            message = params.get('message', [''])[0]

            # Відправляємо дані на Socket сервер через UDP
            udp_client_send({'username': username, 'message': message})

            self.send_response(302)
            self.send_header('Location', '/message.html')
            self.end_headers()



# UDP сокет сервер для обробки даних
def udp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('localhost', SOCKET_PORT))
        print(f"Socket server running on port {SOCKET_PORT}")

        while True:
            data, _ = s.recvfrom(1024)
            message_dict = json.loads(data.decode('utf-8'))
            save_to_json(message_dict)

# Функція для збереження даних у файл data.json
def save_to_json(data):
    timestamp = str(datetime.now())
    with open(DATA_FILE, 'r+') as f:
        content = json.load(f)
        content[timestamp] = data
        f.seek(0)
        json.dump(content, f, indent=4)

# Функція для відправлення даних на Socket сервер
def udp_client_send(data):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        message = json.dumps(data).encode('utf-8')
        sock.sendto(message, ('localhost', SOCKET_PORT))

# Запуск HTTP сервера у потоці
def start_http_server():
    Handler = CustomHTTPRequestHandler
    with socketserver.TCPServer(("", HTTP_PORT), Handler) as httpd:
        print(f"Serving HTTP on port {HTTP_PORT}")
        httpd.serve_forever()

# Основна функція для запуску обох серверів у потоках
def main():
    http_thread = threading.Thread(target=start_http_server)
    socket_thread = threading.Thread(target=udp_server)

    http_thread.start()
    socket_thread.start()

    http_thread.join()
    socket_thread.join()

if __name__ == '__main__':
    main()