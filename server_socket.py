import socket,json
# import multiprocessing
import threading
import os
import datetime
import claude_web
import sys
from reviews_analysis import ChatGPTReviewAnalyzer 
from database_handler import DatabaseHandler
from socket_manager import SocketManager 
from reviews_analyze_model import ReviewsAnalyzeModel
import logging
# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
SERVER_ADDRESS = ('0.0.0.0', 12345)

def ensure_string_ends_with_brace(s):
    if s.endswith("\"}"):
        pass
    elif s.endswith("\" }"):
        pass
    elif s.endswith("\"\n}"):
        pass
    elif s.endswith("}"):
        s = s[:-1] + "\"}"      
    elif s.endswith("\"") or s.endswith("\" "):
        s += "}"   
    else:
        s += "\"}"
    return s

def is_valid_json(data):
    required_fields = ['file_name', 'file_size', 'key', 'type', 'host']
    if not all(field in data for field in required_fields):
        return False

    if not isinstance(data['file_name'], str):
        return False

    if not isinstance(data['file_size'], int):
        return False

    if not isinstance(data['key'], str):
        return False
    
    if not isinstance(data['type'], str):
        return False
    
    if not isinstance(data['host'], str):
        return False
    
    return True


# Define a function to handle a client connection
def handle_client(client_socket, client_address):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"Connection from {client_address}")

    """ Receiving the filename from the client. """
    try:
        file_info_json = client_socket.recv(1024).decode()
        logging.info(f"receive raw data from {client_address}:{file_info_json}")
        # Deserialize the JSON data to a dictionary
        file_info = json.loads(file_info_json)
        if not is_valid_json(file_info):
            raise ValueError("Invalid JSON data")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[ERROR] Invalid data received: {e}")
        client_socket.send("Invalid data format".encode())
        client_socket.close()
        return
    
    # Extract filename and size from the dictionary
    file_name = file_info['file_name']
    file_size = int(file_info['file_size'])
   
    # Access the "prompt" parameter from the request and print it
    key = file_info['key'] 
    type = file_info['type'] 
    host = file_info['host']
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[DEBUG] {timestamp}:file_info: {file_info}")

    db = DatabaseHandler()
    db.connect()

    # Checking user access
    user_details = db.is_user_access_valid(key)
    db.close()
    if user_details:
        print(f"User ID: {user_details[0]}, User Name: {user_details[1]}")
        client_socket.send(f"valid_access".encode())
    else:
        client_socket.send(f"illegal_key".encode())
        print("Access not valid or user does not exist.")
        client_socket.close()
        return


    # Ensure the folder exists, create it if necessary
    os.makedirs('THD_VOC_Bot_Temp', exist_ok=True)

    # Save the file to the specified folder with its original filename
    file_path = os.path.join('THD_VOC_Bot_Temp', file_name)
    

    # Print the file path where the uploaded file is saved
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[DEBUG] {timestamp}:File saved at: {file_path}")

    
    # Create/Open a file for writing the received data
    with open(file_path, 'wb') as file:
        i = 0
        recv_length = 0
        while True:
            data = client_socket.recv(65535)  # Receive data in 1KB chunks
            if not data:
                break
            file.write(data)
            recv_length += len(data)
            if recv_length > MAX_FILE_SIZE:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[ERROR] {timestamp}:data chunk {i} received, length:{len(data)}, total receive lengt: {recv_length}, too big, close communication")
                file.close()
                client_socket.close()
                return

            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[DEBUG] {timestamp}:data chunk {i} received, length:{len(data)}, total receive lengt: {recv_length}")
            client_socket.send(f"data chunk {i} received: {len(data)}\n".encode())
            i += 1
            if file_size == recv_length:
                break
    file.close()
   
    if os.path.getsize(file_path) == file_size:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[DEBUG] {timestamp}:receive file sucess")
    else:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[ERROR] {timestamp}:receive file fail")

    analyzer = ReviewsAnalyzeModel(host)
    result = analyzer.analyze_reviews_from_file(file_path,type =type, product_name = file_name)
    logging.info(result)
    if result['status']:
        response = result['data']['analysis_result']
        model=  result['data']['metadata']['model']
        finish_reason =result['data']['metadata']['finish_reason']
        token_input =result['data']['metadata']['token_input']
        token_output =result['data']['metadata']['token_output']
        error_code = ''
        ret_code = 200
    else:
        response = ''
        model=  ''
        finish_reason =''
        token_input = 0
        token_output = 0
        error_code = result['message']
        ret_code = 500

    # log_data = {
    #     'product_link': file_name,
    #     'analysis_success': result['status'],
    #     'analysis_result': response,
    #     'error_code': error_code,
    #     'model':model,
    #     'finish_reason':finish_reason,
    #     'token_input': token_input,
    #     'token_output': token_output
    # }
    # db.update_visit_log(None,log_data, user_id = user_details[0])

    # Remove '\n'
    response = response.replace('\n', '')

    # Remove '%'
    response = response.replace('%', '')

    # Remove '\\n\\n'
    response = response.replace('\\n\\n', '')

    # if chat_reply.model:
    #     model = chat_reply.model
    # else:
    #     model =None

    # if chat_reply.choices[0].finish_reason:
    #     finish_reason = chat_reply.choices[0].finish_reason
    # else:
    #     finish_reason = None
        
    
    # if chat_reply.usage:
    #     token_input = chat_reply.usage['prompt_tokens']
    #     token_output = chat_reply.usage['completion_tokens']
    # else:
    #     token_input = 0
    #     token_output = 0

    # Inserting a visit log
    log_data = {
        'user_id': user_details[0],  # Example values
        'user_name': user_details[1],
        'product_link': file_name,
        'analysis_success': 1,
        'analysis_result': response,
        'error_code': 'None',
        'model':model,
        'finish_reason':finish_reason,
        'token_input': token_input,
        'token_output': token_output
    }
    db = DatabaseHandler()
    db.connect()
    db.insert_visit_log(log_data)
    db.update_user_usage(user_id=user_details[0], token_usage_increment=token_input+token_output)
    db.close()

    result = {'success':True, 'response':response}
    # result_json = json.dumps(result)
    result_str = str(result)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[DEBUG] {timestamp}:result_str:{result_str}")
    mode_str = f"analysis:{len(result_str)}"
    client_socket.send(mode_str.encode())
    client_respond = client_socket.recv(1024)
    print(f"[client]:{client_respond}")
    client_socket.send(result_str.encode())
    respond_result = client_socket.recv(1024)
    print(f"[client]:{respond_result}")
     # Close the client socket
    client_socket.close()
    print(f"client {client_address} closed")

    sys.stdout.flush()
    sys.stderr.flush()


def claude_(prompt,file_path):
    cookie = "sessionKey=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"
    claude = claude_web.Client(cookie)
    new_chat = claude.create_new_chat()
    conversation_id = new_chat['uuid']
    print(conversation_id)
    response = claude.send_message(prompt, conversation_id,attachment=file_path,timeout=600)
    # print(response)
    return response

def gpt_agent(key,file_path,type):
    assistant = ChatGPTReviewAnalyzer(key,host='closeai')
    result = assistant.analyze_batch_reviews_from_file(file_path,type)
    return result

def gpt_offcial(key,file_path,type):
    assistant = ChatGPTReviewAnalyzer(key, host='openai')
    result = assistant.analyze_batch_reviews_from_file(file_path,type)
    return result

def txt2list(file_path):
    # Initialize an empty list to store the reviews
    reviews = []
    possible_new_review = False
    with open(file_path, 'r',encoding='utf-8') as file:
        # Initialize an empty dictionary to store the current review
        current_review = {}
        
         # Loop through each line in the file
        for line in file:
            line = line.strip()
            
            # If the line is empty, it indicates the end of a review
            if not line:
                possible_new_review = True
            else:
                # Check if the line contains a colon (':')
                if ':' in line:
                    if possible_new_review:
                        # Append the current review dictionary to the list
                        reviews.append(current_review)
                        # Reset the current review dictionary for the next review
                        current_review = {}

                    # Split the line into key and value using ': ' as the separator
                    try:
                        key, value = line.split(': ', 1)
                        current_review[key] = value
                    except Exception as e:
                        print(e)
                        print(line)
                        # current_review[key]= "None"

                else:
                    # If the line doesn't contain a colon, append it to the current content value
                    current_review[key] += "\n" + line if key in current_review else line

                possible_new_review = False
                
        reviews.append(current_review)
    # print(reviews)    
    return reviews

if __name__ == '__main__':
    # Define server address and port
    server_address = ('0.0.0.0', 12345)

    # Create a socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the server address
    server_socket.bind(server_address)

    # Listen for incoming connections
    server_socket.listen(5)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[DEBUG] {timestamp}:Server is listening...")

    DatabaseHandler.initialize_pool(host="localhost", database="pso_voc_tool", user="root", password="")

    while True:
        # Accept a connection
        client_socket, client_address = server_socket.accept()

        # Create a new process to handle the client
        thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        thread.start()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[DEBUG] {timestamp}:[ACTIVE CONNECTIONS] {threading.active_count() - 1}")



