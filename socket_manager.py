
import struct
import os
import socket
import json
import logging
# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
class SocketManager:
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
    HEADER_SIZE = 4  # Size of the header in bytes (for storing message length)
    CHUNK_SIZE = 65535  # Size of each file chunk
    ACK_STRING = 'ACK'
    MAX_MESSAGE_SIZE = 2 * 1024

    def __init__(self, my_socket):
        self.socket = my_socket
    def send_command(self,command, data):
        message = {
            'command': command,
            'data': data,
        }
        encoded_message = json.dumps(message).encode()
        message_length = len(encoded_message)
        header = struct.pack('!I', message_length)  # Create a 4-byte header
        try:
            self.socket.sendall(header + encoded_message)
            self.socket.settimeout(3)
            reply = self.socket.recv(1024).decode()
            if self.ACK_STRING in reply:
                logging.info(f"{reply}")
            else:
                logging.error(f"{reply}")
                return False
        except socket.timeout:
            logging.error("Timeout occurred")
            return False
        except Exception as e:
            logging.error(f"An error occurred - {str(e)}")
            return False
        
        return True

    def receive_command(self):
        try:
            header = self.socket.recv(self.HEADER_SIZE)
            if not header:
                return None
            message_length = struct.unpack('!I', header)[0]
            if message_length > self.MAX_MESSAGE_SIZE:
                return None
            full_message = b''
            while len(full_message) < message_length:
                chunk = self.socket.recv(message_length - len(full_message))
                if not chunk:
                    return None  # Connection closed or error
                full_message += chunk

            if len(full_message) != message_length:
                return None
            message_dict = json.loads(full_message.decode())
            self.socket.send(self.ACK_STRING.encode())
            return message_dict
        except Exception as e:
            logging.error(f"An error occurred - {str(e)}")
            return None

    def send_file(self, file_path):
        file_size  = os.path.getsize(file_path)
        max_retries = 3  # Maximum number of retries for each chunk

        # Send the total file size first
        try:
            self.socket.sendall(struct.pack('!I', file_size))
            self.socket.settimeout(5)
            reply = self.socket.recv(1024).decode()
            if self.ACK_STRING not in reply:
                logging.error(f"NO ACK - {str(reply)}")
                return False
        except socket.timeout:
            logging.error("Timeout occurred")
            return False

        try:
            with open(file_path, 'rb') as file:
                i = 0
                while True:
                    chunk = file.read(self.CHUNK_SIZE)  # Read and send in 1KB chunks
                    if not chunk:
                        break
                    header = struct.pack('!I', len(chunk))
                    logging.info(f"ready to send chunk {i}, size is {len(chunk)}")
                    retries = 0
                    while retries < max_retries:
                        try:
                            self.socket.sendall(header + chunk)  # Send header and chunk
                            # Wait for an acknowledgement
                            self.socket.settimeout(5)
                            reply = self.socket.recv(1024).decode()
                            if self.ACK_STRING in reply:
                                logging.info(f"received ACK when send chunk {i}")
                                break  # Chunk sent successfully, proceed to next chunk
                        except socket.timeout:
                            logging.error(f"Timeout occurred when send chunk {i}, retrying ({retries + 1}/{max_retries})")
                            retries += 1
                        except Exception as e:
                            logging.error(f"An error occurred when send chunk {i} - {str(e)}, retrying ({retries + 1}/{max_retries})")
                            retries += 1
                    if retries == max_retries:
                        logging.error(f"Maximum retries reached, failed when send chunk {i}")
                        return False
                    i+=1
                    logging.info(f"success to send chunk {i}")
        except socket.timeout:
            logging.error("Timeout occurred")
            return False
        except Exception as e:
            logging.error(f"An error occurred - {str(e)}")
            return False
  
        return True

    def receive_file(self, file_path):
        # Receive the total file size first
        header = self.socket.recv(self.HEADER_SIZE)
        self.socket.send(self.ACK_STRING.encode())
        total_file_size = struct.unpack('!I', header)[0]
        logging.info(f"ready to receive the new file , file size is: {total_file_size}")
        if total_file_size > self.MAX_FILE_SIZE:
            logging.error(f"file size is to big, it is: {total_file_size}, forbid to receive")
            return False
        i = 0
        try:
            with open(file_path, 'wb') as file:
                received_size  = 0
                while received_size < total_file_size:
                    header = self.socket.recv(self.HEADER_SIZE)
                    if not header:
                        logging.error("no header found")
                        return False
                    chunk_length = struct.unpack('!I', header)[0]
                    logging.info(f"ready to receive the new file chunk {i}, chunk size is: {chunk_length}")
                    full_chunk = b''
                    while len(full_chunk) < chunk_length:
                        chunk = self.socket.recv(chunk_length - len(full_chunk))
                        if not chunk:
                            logging.error('Connection closed or error')
                            return False
                        full_chunk += chunk
                        logging.info(f"received the new file chunk {i}, chunk size is: {len(chunk)}")

                    if len(full_chunk) != chunk_length:
                        logging.error('Incomplete chunk received')
                        return False
                    
                    received_size  += len(full_chunk)
                    file.write(full_chunk)

                    if received_size  > self.MAX_FILE_SIZE:
                        logging.error(f"data chunk {i} received, length:{len(full_chunk)}, total receive lengt: {received_size }, too big, close communication")
                        return False
                    if received_size > total_file_size:
                        logging.error("received file bigger than what want to send")
                        return False
                    i += 1
                    logging.info(f"received the whole file chunk {i}, chunk size is: {len(full_chunk)}")
                    self.socket.send(self.ACK_STRING.encode())
        
        except Exception as e:
            logging.error(f"An error occurred - {str(e)}")
            return False
        
        logging.info(f"success to receive the file")
        return True

if __name__ == "__main__":
    TESTER = "server"
    # TESTER = "client"
    HOST = '43.134.112.182'
    PORT = 5000
    if TESTER == "server":
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', PORT))
        server_socket.listen(1)
        logging.info(f"Server listening on port {PORT}")

        client_socket, addr = server_socket.accept()
        logging.info("Connection from {addr}")

        socket_manager = SocketManager(client_socket)
        message = socket_manager.receive_command()
        if message is None:
            logging.error("message is none") 
        logging.info(f"Received command: {message}")
        if message['command'] == 'reviews_analysis':
            key = message['data']['key'] 
            type = message['data']['type'] 
            host = message['data']['host']
            file_name = message['data']['file_name']
            logging.info(f"key = {key},type={type},host={host},file_name={file_name} ")
            logging.info("start to receive file")
            ret = socket_manager.receive_file('recei_file_socket_manager.txt')
            if ret is False:
                logging.error("fail to receive file")
            else:
                logging.info("success to receive file")
        client_socket.close()
        server_socket.close()
    else:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        socket_manager = SocketManager(client_socket)
        # Test send_command
        test_data = {'key': "sk-xxxxxx", 'type':'overall', 'host' : "remote3",'file_name':os.path.basename("Hampton Bay IndoorOutdoor 12-Light 24 ft. Smart Plug-in Edison Bulb RGBW Color Changing LED String Light Powered by Hubspace HB-10521-HS - The Home Depot.txt")}
        ret = socket_manager.send_command('reviews_analysis', test_data)
        logging.info(f"send ret: {ret}")
        logging.info("start to send")
        ret = socket_manager.send_file('C:/Users/d87wvh/THD_VOC_Bot/Hampton Bay IndoorOutdoor 12-Light 24 ft. Smart Plug-in Edison Bulb RGBW Color Changing LED String Light Powered by Hubspace HB-10521-HS - The Home Depot.txt')
        logging.info("finish to send")
        client_socket.close()