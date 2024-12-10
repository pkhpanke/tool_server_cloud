import socketserver
from http.server import BaseHTTPRequestHandler
import json
import logging
import time
import base64
import hashlib
import os
from database_handler import DatabaseHandler
from reviews_analyze_model import ReviewsAnalyzeModel
import ssl

UPLOAD_FOLDER = 'THD_VOC_Bot_Temp'

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        logging.info(f"Received POST request on path: {self.path}")
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        # logging.info(f"post_data:  {post_data}")
        data = json.loads(post_data)

        if self.path == '/analyze_file':
            self.handle_analyze_file(data)
        elif self.path == '/login':
            self.handle_login(data)
        elif self.path == '/get_analysis_result':
            self.handle_get_analysis_result(data)
        else:
            self.handle_not_found()


    def handle_analyze_file(self, data):
        try:
            db = None  # Initialize db to None
            if not isinstance(data, dict) or not data.get('key') or not data.get('session_id') or not data.get('type') or not data.get('host') or not data.get('product_name') or not data.get('filename') or not data.get('file_content'):
                logging.warning("Invalid or missing data")
                self.send_response(401)
                self.end_headers()
                response = "Invalid or missing data"
                self.wfile.write(bytes(response, "utf-8"))
                return  # Early return on invalid data
            product_name = data['product_name']
            file_content_base64 = data['file_content']
            filename = data['filename']
            key = data['key']
            session_id = data['session_id']
            host = data['host']
            type = data['type']
            # Ensure the folder exists, create it if necessary
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if file_path and file_content_base64:
                # Decode the file content from base64
                file_content = base64.b64decode(file_content_base64)
                with open(file_path, 'wb') as file:
                    file.write(file_content)
                
                logging.info(f"File {filename} uploaded successfully, Size: {len(file_content)} bytes")
                logging.info(f'File saved at:, {file_path}')

            db = DatabaseHandler()
            db.connect()
            logging.info("Inite a database connection")
            ret = db.check_sessionid(session_id)
            db.close()
            logging.info("close a database connection")
            db = None
            if ret is False:
                # Return a JSON response with the error details
                self.send_response(500)
                self.end_headers()
                session_json = {"error": "wrong session", "analysis_success": False}
                response = json.dumps(session_json)
                self.wfile.write(bytes(response, "utf-8"))
                return 
            analyzer = ReviewsAnalyzeModel(host)
            result = analyzer.analyze_reviews_from_file(file_path,type =type, product_name = product_name)
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
            log_data = {
                'product_link': filename,
                'analysis_success': result['status'],
                'analysis_result': response,
                'error_code': error_code,
                'model':model,
                'finish_reason':finish_reason,
                'token_input': token_input,
                'token_output': token_output
            }
            db = DatabaseHandler()
            db.connect()
            logging.info("Inite a database connection")
            db.update_visit_log(session_id,log_data)
            db.update_user_usage(user_id = None, token_usage_increment=token_input+token_output, user_key=key)
            db.close()
            logging.info("close a database connection")
            db = None
            self.send_response(200)
            self.end_headers()
            session_json = {"analysis_success": result['status'], "analysis_result": response, "error": result['message']}
            response = json.dumps(session_json)
            self.wfile.write(bytes(response, "utf-8"))
            return 
        except Exception as e:
            # Log the exception for debugging purposes
            logging.error(f"An error occurred: {str(e)}")
            # Return a JSON response with the error details
            self.send_response(500)
            self.end_headers()
            session_json = {"error": str(e), "analysis_success": False}
            response = json.dumps(session_json)
            self.wfile.write(bytes(response, "utf-8"))
            return
        
        finally:
            if db is not None:  # Check if db is defined
                db.close()
                logging.info("close a database connection")


    def handle_login(self, data):
        if not isinstance(data, dict) or not data.get('key'):
            logging.warning("Invalid or missing data")
            self.send_response(401)
            self.end_headers()
            response = "Invalid or missing data"
            self.wfile.write(bytes(response, "utf-8"))
            return  # Early return on invalid data
        
        db = DatabaseHandler()
        db.connect()
        logging.info("Inite a database connection")
        key = data['key']
        user_details = db.is_user_access_valid(key)
        if user_details:
            logging.info(f"User ID: {user_details[0]}, User Name: {user_details[1]}")
            session_id = generate_session_id(key)
            db.insert_visit_log_login(user_details[0], user_details[1], session_id)
            # Return HTTP 200 status and JSON data with session_id
            db.close()
            logging.info("close a database connection")
            self.send_response(200)
            self.end_headers()
            session_json = {"session_id": session_id}
            response = json.dumps(session_json)
            self.wfile.write(bytes(response, "utf-8"))

        else:
            logging.error("Access not valid or user does not exist.")
            db.close()
            logging.info("close a database connection")
            self.send_response(401)
            self.end_headers()
            response = "Access not valid or user does not exist."
            self.wfile.write(bytes(response, "utf-8"))

    def handle_get_analysis_result(self, data):
        if not isinstance(data, dict) or not data.get('session_id'):
            logging.warning("Invalid or missing data")
            self.send_response(401)
            self.end_headers()
            response = "Invalid or missing data"
            self.wfile.write(bytes(response, "utf-8"))
            return  # Early return on invalid data
        db = None  # Initialize db to None
        try:
            session_id = data['session_id']

            db = DatabaseHandler()
            db.connect()
            logging.info("Inite a database connection")
            ret = db.check_sessionid(session_id)
            if ret is False:
                db.close()
                logging.info("close a database connection")
                db = None
                self.send_response(500)
                self.end_headers()
                data_json = {"error": "wrong session", "analysis_success": False}
                response = json.dumps(data_json)
                self.wfile.write(bytes(response, "utf-8"))
                return 
            result = db.get_analysis_result_fromdatabase(session_id)
            db.close()
            logging.info("close a database connection")
            db = None
            if result is None or result == '':
                self.send_response(500)
                self.end_headers()
                data_json = {"error": "please waiting for a moment", "analysis_success": False}
                response = json.dumps(data_json)
                self.wfile.write(bytes(response, "utf-8"))
                return 

            logging.info(result)
            self.send_response(200)
            self.end_headers()
            data_json = {"analysis_success": True, "analysis_result": result, "error": None}
            response = json.dumps(data_json)
            self.wfile.write(bytes(response, "utf-8"))
            return 
        except Exception as e:
            # Log the exception for debugging purposes
            logging.error(f"An error occurred: {str(e)}")
            # Return a JSON response with the error details
            self.send_response(500)
            self.end_headers()
            data_json = {"error": str(e), "analysis_success": False}
            response = json.dumps(data_json)
            self.wfile.write(bytes(response, "utf-8"))
            return
        finally:
            if db is not None:  # Check if db is defined
                db.close()
                logging.info("close a database connection")

    def handle_not_found(self):
        logging.error(f"Path not found: {self.path}")
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"404 Not Found")

def generate_session_id(key):
    # Get the current timestamp
    timestamp = str(time.time())

    # Combine the key with the timestamp
    combined = key + timestamp

    # Create a SHA-256 hash of the combined string
    hash_object = hashlib.sha256(combined.encode())
    hashed_string = hash_object.digest()

    # Encode the hash in base64
    encoded = base64.b64encode(hashed_string)

    # Optionally, you can truncate or adjust the length. Here, we keep it as is
    # since base64 encoding of SHA-256 hash will be around 44 characters.
    return encoded.decode('utf-8')


class HTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def run(server_class=HTTPServer, handler_class=HTTPHandler, port=5255,certfile='/home/lighthouse/hubspace_cloud_server/ssl_key/hubspace.run.place_nginx/hubspace.run.place_bundle.crt', keyfile='/home/lighthouse/hubspace_cloud_server/ssl_key/hubspace.run.place_nginx/hubspace.run.place.key'):
    server_address = ('0.0.0.0', port)
    httpd = server_class(server_address, handler_class)

    # Wrap the HTTP server with SSL
    httpd.socket = ssl.wrap_socket(httpd.socket, keyfile=keyfile, certfile=certfile, server_side=True)

    logging.info(f"Starting httpd server on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    DatabaseHandler.initialize_pool(host="localhost", database="pso_voc_tool", user="root", password="")
    run()