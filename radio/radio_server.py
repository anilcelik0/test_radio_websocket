import socket
import time

def start_radio_server():
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 8001)  # Bind the socket to port 8001
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(1)
    print("Radio server started on port 8001...")

    while True:
        # Wait for a connection
        connection, client_address = sock.accept()
        try:
            print(f"Connection from {client_address}")
            # Simulate streaming audio data
            with open("radio/darth_vader.mpeg", "rb") as file: # Simulate audio data
                data = file.read()
            connection.sendall(data)
            time.sleep(1)  # Simulate a delay between packets
        except ConnectionResetError:
            print(f"Connection reset by peer: {client_address}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Clean up the connection
            connection.close()
