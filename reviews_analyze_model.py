import json
import datetime
import claude_web
import sys
from reviews_analysis import ChatGPTReviewAnalyzer 
from GPT_reviews_analyzer import GPTReviewsAnalyzer
from database_handler import DatabaseHandler

class ReviewsAnalyzeModel:
    def __init__(self,host) -> None:
        self.host = host
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


    # Define a function to handle a client connection
    def analyze_reviews_from_file(self, file_path, type = 'overall', prompt = None, product_name = None):
        try:
            if prompt is not None:
                # prompt_text = prompt
                pass
            else:
                if type == 'negative':
                    prompt_text = """You will be presented with negative part of customer reviews and your job is to identify and list below 3 sections.
                    1. top 5 most mentioned issues with their number of reviews mentioned.
                    2. top 5 dislike or complaint from customer with their number of reviews mentioned. 
                    3. point of view and valuable summary (more than 200 words).
                    Please aware use a json data to contain these information. make the section title as first level name of json data, the items and mentioned number as second level name and value of json data."""
                else:
                    prompt_text = """You will analyze customer reviews and organize the findings into a JSON structured format with 5 key sections. The sections are:

                1. Customer Persona: Provide a summary of the typical customer based on the reviews.

                2. Usage Scenarios: Identify different scenarios in which the product is used, along with the count of unique reviews mentioning each scenario.

                3. Positive Aspects (Pros): Identify the most frequently mentioned positive aspects of the product, along with the count of unique reviews mentioning each pro.

                4. Negative Aspects (Cons): Identify the most frequently mentioned negative aspects of the product, along with the count of unique reviews mentioning each con.

                5. Suggestions for Improvement: Conclude the suggestions for product improvement.
                       
    For each section (except Customer Persona and Suggestions for Improvement), provide:
        - The count of unique reviews mentioning each item.
                       
    Counting and categorization guidelines:
        - Group similar concepts expressed in different ways under a single item.
        - Before finalizing, verify all counts by re-analyzing the reviews.

    For each section, use the section title as the first-level key in the JSON data. The detailed items and The count of unique reviews mentioning each item. should be formatted as second-level key-value pairs within each section. Here is an example format for output:
    ```
        {
        "Customer Persona": {
            "description": "A tech-savvy homeowner who enjoys the convenience of modern, smart home technology. This customer appreciates the ability to control home lighting remotely or via voice commands, often using the bulbs for both practical and mood lighting purposes. They value energy efficiency and are interested in easy-to-install solutions that integrate seamlessly into their home environment."
        },
        "Usage Scenarios": {
            "Home interior lighting": 38,
            "Children's room": 22,
            "Outdoor lighting": 20,
            "Holiday and mood lighting": 15,
            "Remote control and automation": 8
        },
        "Positive Aspects (Pros)": {
            "Easy app control": 30,
            "Voice assistant compatibility": 20,
            "Variety of colors and settings": 25,
            "Energy efficient": 19,
            "Easy installation": 18
        },
        "Negative Aspects (Cons)": {
            "Wi-Fi connection drops": 28,
            "Limited outdoor functionality": 23,
            "Occasional humming noise at high brightness": 15,
            "App requires frequent logins": 12,
            "Compatibility issue with certain light fixtures": 4,
            "Color brightness not as expected": 3
        },
        "Suggestions for Improvement": {
            "suggestion": "Improve Wi-Fi stability and outdoor functionality, reduce noise at high brightness, streamline the app experience, enhance fixture compatibility, and improve color brightness. Maintain and highlight ease of installation, app control, voice assistant compatibility, variety of colors, and energy efficiency."
        }
    }
    ```"""
            # reviews_list = txt2list(file_path)
            if self.host == 'remote1':
                return {
                    "status": False,
                    "message": f"invalid host {self.host}",
                    "data": None
                }
                response = self.claude_(prompt_text, file_path)
            elif self.host == 'remote2':
                chat_reply = self.gpt_agent("sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV", file_path,type, product_name = product_name)
                response = chat_reply
            elif self.host == 'remote3':
                chat_reply = self.gpt_openai("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", file_path,type, product_name = product_name)
                response = chat_reply
            else:
                return {
                    "status": False,
                    "message": f"invalid host {self.host}",
                    "data": None
                }
    
                # Assuming response and other variables are set correctly
            return response
        
        except FileNotFoundError as e:
            return {
                "status": False,
                "message": f"File not found: {e}",
                "data": None
            }

        except ConnectionError as e:
            return {
                "status": False,
                "message": f"Failed to connect to remote service: {e}",
                "data": None
            }

        except Exception as e:
            # Generic exception handler for any other unforeseen errors
            return {
                "status": False,
                "message": f"An unexpected error occurred: {e}",
                "data": None
            }

    def claude_(self,prompt,file_path):
        cookie = "sessionKey=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"
        claude = claude_web.Client(cookie)
        new_chat = claude.create_new_chat()
        conversation_id = new_chat['uuid']
        print(conversation_id)
        response = claude.send_message(prompt, conversation_id,attachment=file_path,timeout=600)
        # print(response)
        return response

    def gpt_agent(self,key,file_path,type,product_name = None):
        assistant = ChatGPTReviewAnalyzer(key,host='closeai')
        result = assistant.analyze_batch_reviews_from_file(file_path,type,product_name = product_name)
        return result

    def gpt_offcial(self,key,file_path,type,product_name = None):
        assistant = ChatGPTReviewAnalyzer(key, host='openai')
        result = assistant.analyze_batch_reviews_from_file(file_path,type,product_name = product_name)
        return result
    
    def gpt_openai(self,key,file_path,type,product_name = None):
        assistant = GPTReviewsAnalyzer(key, host='openai')
        result = assistant.split_and_analyze_reviews_file(file_path,type = type,product_name = product_name)
        return result

    def txt2list(self,file_path):
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
    DatabaseHandler.initialize_pool(host="localhost", database="pso_voc_tool", user="root", password="")
