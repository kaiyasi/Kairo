import unittest
import socket
import threading
import time
from socket_server import start_socket_server

class TestSocketServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start socket server in background thread"""
        cls.server_thread = threading.Thread(target=start_socket_server)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(1)  # Give server time to start

    def test_ping_response(self):
        """Test that ping command returns pong"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 9000))
            s.send(b'ping')
            response = s.recv(1024).decode('utf-8')
            self.assertEqual(response, 'pong')

    def test_other_response(self):
        """Test that other commands return ok"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 9000))
            s.send(b'hello')
            response = s.recv(1024).decode('utf-8')
            self.assertEqual(response, 'ok')

    def test_empty_response(self):
        """Test that empty command returns ok"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 9000))
            s.send(b'')
            response = s.recv(1024).decode('utf-8')
            self.assertEqual(response, 'ok')

if __name__ == '__main__':
    unittest.main()