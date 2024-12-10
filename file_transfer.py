import socket
import hashlib

class FileTransfer:
    def __init__(self, host, port, role):
        self.host = host
        self.port = port
        self.role = role  # 'client' or 'server'
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if role == 'server':
            self.sock.bind((host, port))
            self.sock.listen(1)
            self.conn, _ = self.sock.accept()
        elif role == 'client':
            self.sock.connect((host, port))

    def send_file(self, file_path):
        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(1024 * 1024)  # 1 MB chunk size
                if not chunk:
                    break
                self.send_chunk(chunk)

        self._send_end_of_file_signal()

    def receive_file(self, file_path):
        with open(file_path, 'wb') as file:
            while True:
                chunk = self._receive_chunk()
                if chunk is None:  # End of file signal received
                    break
                file.write(chunk)

    def send_chunk(self, chunk):
        hash_digest = hashlib.sha256(chunk).hexdigest()
        size = len(chunk).to_bytes(4, 'big')  # 4 bytes to represent the size
        data = size + hash_digest.encode() + chunk
        self._send_data(data)

        if not self._wait_for_ack():
            self.send_chunk(chunk)  # Resend the chunk

    def _receive_chunk(self):
        size_data = self._recv_data(4)  # Receive the size of the chunk first
        if not size_data:
            return None

        size = int.from_bytes(size_data, 'big')
        data = self._recv_data(size + 64)  # Adjusted to receive the exact chunk size + hash size

        if data == b'EOF':  # End of file signal
            return None

        hash_received = data[:64].decode()
        chunk = data[64:]

        if hashlib.sha256(chunk).hexdigest() == hash_received:
            self._send_ack(True)
            return chunk
        else:
            self._send_ack(False)
            return self._receive_chunk()

    def _send_data(self, data):
        if self.role == 'client':
            self.sock.sendall(data)
        elif self.role == 'server':
            self.conn.sendall(data)

    def _recv_data(self, bufsize):
        data = b''
        while len(data) < bufsize:
            packet = self.conn.recv(bufsize - len(data)) if self.role == 'server' else self.sock.recv(bufsize - len(data))
            if not packet:
                return None
            data += packet
        return data

    def _send_ack(self, ack_status):
        ack_message = 'OK' if ack_status else 'RESEND'
        self._send_data(ack_message.encode())

    def _wait_for_ack(self):
        ack = self._recv_data(2)  # Assuming 'OK' or 'RE' as acknowledgment message
        return ack.decode() == 'OK'

    def _send_end_of_file_signal(self):
        self._send_data(b'EOF')

    def close(self):
        if self.role == 'server':
            self.conn.close()
        self.sock.close()

if __name__ == "__main__":
    user = "server"
    if user == "server":
        server = FileTransfer('0.0.0.0', 5000, 'server')
        server.receive_file('received_file.txt')
        server.close()
    else:
        client = FileTransfer('43.134.112.182', 5000, 'client')
        client.send_file('C:/Users/d87wvh/THD_VOC_Bot/Amerimax Home Products Hoover Dam 3 ft. Gray Metal Mesh Gutter Guard 6380 - The Home Depot.txt')
        client.close()
