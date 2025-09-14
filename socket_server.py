import socket
import threading
import logging
import asyncio
import os
import sys
from bot_main import main as bot_main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_client(client_socket, addr):
    """Handle individual client connections"""
    try:
        data = client_socket.recv(1024).decode('utf-8').strip()
        logger.info(f"Received from {addr}: {data}")

        if data == "ping":
            response = "pong"
        else:
            response = "ok"

        client_socket.send(response.encode('utf-8'))
        logger.info(f"Sent to {addr}: {response}")

    except Exception as e:
        logger.error(f"Error handling client {addr}: {e}")
    finally:
        client_socket.close()

def start_socket_server():
    """Start the socket server for health checks"""
    HOST = '0.0.0.0'
    PORT = 9000

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)

        logger.info(f"Socket server listening on {HOST}:{PORT}")

        while True:
            client_socket, addr = server_socket.accept()
            logger.info(f"Connection from {addr}")

            # Handle each client in a separate thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, addr)
            )
            client_thread.daemon = True
            client_thread.start()

    except Exception as e:
        logger.error(f"Socket server error: {e}")
    finally:
        if 'server_socket' in locals():
            server_socket.close()

def main():
    """Main function to start both socket server and Discord bot"""
    logger.info("Starting Kairo services...")

    # Start socket server in a separate thread
    socket_thread = threading.Thread(target=start_socket_server)
    socket_thread.daemon = True
    socket_thread.start()

    # Start Discord bot
    try:
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()