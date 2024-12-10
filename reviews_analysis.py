import openai
import requests,os
import json
import tiktoken
from typing import List, Dict, Tuple

# below install is important
# pip install urllib3==1.25.11
# self.models_list = [
#     ["gpt-3.5-turbo", 4096],
#     ["gpt-3.5-turbo-16k", 16384],
#     ["gpt-4", 8192],
#     ["gpt-4-32k", 32768]
# ]
# API_key="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"
API_key='sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV'
# API_key='sk-Q3d6OMRA5Zi1qT3R4069D5E3F9Bb4958B145A85d49Cb7e63'
proxies = {
    'http': 'http://127.0.0.1:9981',
    'https': 'https://127.0.0.1:9981',
    'socks5':'127.0.0.1:9981',
}
# requests.Session().proxies = proxies
# proxy = "http://127.0.0.1:9981"  # 代理

system_info_overall = {"role": "system", "content": """You will analyze customer reviews and organize the findings into a JSON structured format with 5 key sections. The sections are:

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
}

system_info_nagetive = {"role": "system", "content": """You will be presented with negative part of customer reviews and your job is to identify and list below 3 sections.
            1. top 5 most mentioned issues with their number of reviews mentioned. 
            2. top 5 dislike or complaint from customer with their number of reviews mentioned. 
            3. point of view and valuable summary (more than 200 words).
Please aware use a json data to contain these information. make the section title as first level name of json data, the items and number as second level name and value of json data."""}

class ChatGPTReviewAnalyzer:
    def __init__(self,key = 'sk-Kbe0RxYjbnfiY8UU0rw0gqYmiOBA45EL8BtzRHSfy12hu3mD@15570',host='closeai'):
        openai.api_key = key
        # openai.proxy = 'http=127.0.0.1:9981'
        self.host = host
        if host == 'closeai':
            openai.api_base = 'https://api.openai-proxy.org/v1'
        else:
            pass
        # openai.api_base = 'https://api.onekey.asia'
        self.history = []
        self.models_list = [
            # ["gpt-3.5-turbo", 3096], #4096, save 1000 tokens for result
            # ["gpt-3.5-turbo-16k", 15000], #16000, save 1000 tokens for result
            ["gpt-4-1106-preview",126000],
        ]
        self.messages = [{"role": "system", "content": """You will be presented with customer reviews and your job is to identify and list below 6 sections.
            1. top 5 most mentioned positive aspects (Pros) with their respective counts
            2. top 5 most mentioned negative aspects (Cons) with their respective counts
            3. top 5 most mentioned issues with their respective counts 
            4. top 5 most Purchase Motivations with their respective counts, 
            5. top 5 most mentioned customer Expectation with their respective counts
            6. top 5 suggestions for improvement. 
            Please aware use a json data to contain these information. list the section as first level of json data, the itmes and mentioned number as second level of json data."""}]
        
    def num_tokens_from_string(self, string: str, encoding_name: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    
    def onekey_method(self,messages):
        apiURL = 'https://api.onekey.asia/v1/chat/completions'
        apiKey = 'sk-Q3d6OMRA5Zi1qT3R4069D5E3F9Bb4958B145A85d49Cb7e63'
        temperature = 0.2
        model = 'gpt-4'
        headers = {
            "Accept":'application/json',
            'Content-Type':'application/json',
            'Authorization':'Bearer'+apiKey
        }
        post = {
            'model':model,
            'temperature':temperature,
            'messages':messages,
        }

        try:
            response = requests.post(
                apiURL,
                headers=headers,
                data = json.dumps(post),
                timeout=None,
                proxies = proxies,
            )
            print(f"response status code:{response.status_code}")
            if response.status_code == 200:
                if response.text:
                    print(response.json())
                else:
                    print("response is empty")
            else:
                print("request failed, response content:",response.text)
        except Exception as e:
            print("error:",e)
    

    def _get_suitable_model(self, text: str) -> str:
        token_count = self.num_tokens_from_string(text, "gpt-3.5-turbo")
        print("token_count: ",token_count)
        for model, limit in self.models_list:
            if token_count <= limit:
                return model
        # raise ValueError("Text too long for available models.")
        return None

    def add_to_history(self, role, content):
        """Add a message to history and maintain the last 5 messages for context."""
        self.history.append({"role": role, "content": content})
        if len(self.history) > 5:  # Limiting to last 5 messages, but you can adjust this as needed
            self.history.pop(0)

    def start_conversation(self):
        """Start a new conversation by clearing the history."""
        self.history = []
        self.add_to_history("system", "You are a helpful assistant.")

    def get_response(self, message):
        total_tokens = sum([self.num_tokens_from_string(msg['content'], "gpt-3.5-turbo") for msg in self.history])
        total_tokens += self.num_tokens_from_string(message, "gpt-3.5-turbo")
        
        selected_model = self.select_model(total_tokens)
        
        self.add_to_history("user", message)
        response = openai.ChatCompletion.create(
            model=selected_model,
            messages=self.history
        )
        
        # Add the model's reply to the history
        self.add_to_history("assistant", response['choices'][0]['message']['content'])
        return response['choices'][0]['message']['content']

    def analyze_review(self, review: str) -> str:
        model_name = self._get_suitable_model(review)
        self.messages.append({"role": "user", "content": f"Analyze the following review: '{review}'"})
        
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=self.messages
        )
        
        # Add the model's response to the message history to retain context
        self.messages.append({
            "role": "assistant",
            "content": response.choices[0].message['content']
        })
        
        # Returning the assistant's reply
        return response.choices[0].message['content']

    def analyze_reviews_from_file(self, filepath: str) -> Dict[str, str]:
        with open(filepath, 'r',encoding='utf-8') as file:
            reviews = file.readlines()
        
        analysis_results = {}
        for review in reviews:
            analysis = self.analyze_review(review.strip())
            analysis_results[review] = analysis
        
        return analysis_results
    
    def analyze_batch_reviews(self, reviews: list) -> str:
        # Combine all reviews into one string for processing
        combined_reviews = " ".join(reviews)
        
        model_name = self._get_suitable_model(combined_reviews)
        self.messages.append({"role": "user", "content": f"Analyze the following batch of reviews: '{combined_reviews}'"})
        
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=self.messages
        )
        
        # Add the model's response to the message history if you want to retain context for future analyses
        self.messages.append({
            "role": "assistant",
            "content": response.choices[0].message['content']
        })
        
        # Returning the assistant's analysis
        return response.choices[0].message['content']
    
    def analyze_batch_reviews_from_string(self, reviews: str) -> str:
        model_name = self._get_suitable_model(reviews)
        self.messages.append({"role": "user", "content": f"Analyze the following batch of reviews: '{reviews}'"})
        
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=self.messages
        )
        # Add the model's response to the message history if you want to retain context for future analyses
        self.messages.append({
            "role": "assistant",
            "content": response.choices[0].message['content']
        })
        
        # Returning the assistant's analysis
        return response.choices[0].message['content']
    def list_convert_to_string(self,data):
        reviews_str =""
        for review in data:
                # Iterate through each review dictionary and write its contents to the file
                for key, value in review.items():
                    reviews_str += (f"{key}: {value}\n")
                reviews_str += ('\n')  # Add a blank line to separate reviews
        # print("-----list_convert_to_string-----", reviews_str)
        return reviews_str
        # print("----------list_convert_to_string",data)
        # return "\n\n".join(
        #     f"Date: {review['Date']}\n Stars: {str(review['Stars'])}\n Title: {review['Title']}\n Content: {review['Content']}\n Reviewer: {review.get('Reviewer', '')}" 
        #     for review in data
        # )
    
    def extract_json(s):
        start_idx = s.find('{')
        if start_idx == -1:
            return None

        brace_count = 0
        for idx, char in enumerate(s[start_idx:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1

            if brace_count == 0:
                return s[start_idx: start_idx + idx + 1]

        return None

    def analyze_batch_reviews_from_list(self, reviews: list, type = 'negative') -> str:
        # confirm the token:
        reviews_string = self.list_convert_to_string(reviews)
        token_count = self.num_tokens_from_string(reviews_string, "gpt-3.5-turbo")
        if type == 'overall':
            system_prompt = system_info_overall
        else:
            system_prompt = system_info_nagetive
        for model, limit in self.models_list:
            print("token count:",token_count,"model:",model)
            section_number = token_count//(limit-1000) + 1
            break

        reviews_number = len(reviews)
        #sub section views
        section_unit = reviews_number // section_number + (reviews_number % section_number) // section_number +(reviews_number % section_number) % section_number
        section = section_number
        print("section number:",section_number,"section unit:",section_unit)
        response_list = []
        response = None
        if section == 1:
            reviews_section = ""
            reviews_section = self.list_convert_to_string(reviews)
            model_name = self._get_suitable_model(reviews_section)
            message = []
            message.append(system_prompt)
            message.append({"role": "user", "content": f"'{reviews_section}'"})
            # print("analyze the reviews: section", section ,". select model: ",model_name,"index from: 0", "to:",reviews_number)
            try:
                response = openai.ChatCompletion.create(
                    model=model_name,
                    messages = message,
                    temperature = 0.02,
                    max_tokens=1024,
                    response_format={ "type": "json_object" }
                )
            except Exception as e:
                print("issue when to connect chatgpt",e)
                return
            print(f"---response.choices[0].message['content']:{response.choices[0].message['content']}")
            return response.choices[0].message['content']
        
        for i in range(section):
            start = i * section_unit
            end = (i+1) * section_unit
            reviews_sub = reviews[start:end]
            # print("analyze the reviews from:",start, "to:",end)
            # Skip if no reviews in this subsection
            if not reviews_sub:
                continue
            
            reviews_section = ""
            reviews_section = self.list_convert_to_string(reviews_sub)
            model_name = self._get_suitable_model(reviews_section)
                
            message = []
            message.append(system_prompt)
            message.append({"role": "user", "content": f"'{reviews_section}'"})
            print("analyze the reviews: section", i ,". select model: ",model_name,"index from:",start, "to:",end)
            # print("section: ",i,". select model: ",model_name,"message: ",message)
            try:
                response = openai.ChatCompletion.create(
                    model=model_name,
                    messages = message
                )

                response_list.append(response.choices[0].message['content'])
                # print("section: ",i," analysis result:",response.choices[0].message['content'])
            except Exception as e:
                print("issue when to connect chatgpt",e)
                return 

        # response_all = "\n\n".join(f"Section {index}:\n[{response}]" for index, response in enumerate(response_list, 1))
        
        response_all = "\n\n".join(response_list)
        # print("responce all",response_all)
        model_name = self._get_suitable_model(response_all)
        message =[
            {
                "role": "system",
                "content": """You will receive several JSON objects representing the analysis of customer reviews. Your task is to merge them into a single cohesive JSON object with the following rules:

                1. Identical Names: If names are identical across different JSONs, combine their values by summing them up.
                2. Similar Names: For names that are not exactly the same but have similar meanings (e.g., "good service" and "excellent services"), their values should be combined.
                3. Final Structure: The resulting output should be a new JSON object containing this merged data.
                4. Top 5 Priority: Retain only the top 5 items for each primary key in the merged JSON, and discard the rest.

                Output only the final merged JSON, without providing any analysis or intermediate steps."""
            },
            {
                "role": "user",
                "content": f"{response_all}"
            }
            ]
        # print("final message: ",message)
    
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages = message,
            temperature = 0.02,
            max_tokens=1024,
            response_format={ "type": "json_object" }
        )
        
        # Returning the assistant's analysis
        return response.choices[0].message['content']


    def analyze_batch_reviews_from_file(self, filepath: str, type = 'negative', prompt = None, product_name = None) -> str:
        with open(filepath, 'r',encoding='utf-8') as file:
            reviews = file.readlines()

        # Combine all reviews into one string for processing
        combined_reviews = " ".join(reviews)
        if prompt is None:
            if type == 'negative':
                system_prompt = system_info_nagetive
            else:
                system_prompt = system_info_overall
        else:
            system_prompt = prompt
        if product_name is not None:
            pre_user_prompt = f"The following are the customer views for product <{product_name}>: \n\n"
        else:
            pre_user_prompt = f"The following are the customer views: \n\n"

        model_name = self._get_suitable_model(combined_reviews)
        print("chosen modle:",model_name)
        messages = []
        messages.append(system_prompt)
        messages.append({"role": "user", "content": f"{pre_user_prompt}```{combined_reviews}```"})
        
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            temperature = 1,
            max_tokens=1024,
            response_format={ "type": "json_object" }
        )
        # Add the model's response to the message history if you want to retain context for future analyses
        # self.messages.append({
        #     "role": "assistant",
        #     "content": response.choices[0].message['content']
        # })
        
        """
        {
            "choices": [
                {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "The 2020 World Series was played in Texas at Globe Life Field in Arlington.",
                    "role": "assistant"
                }
                }
            ],
            "created": 1677664795,
            "id": "chatcmpl-7QyqpwdfhqwajicIEznoc6Q47XAyW",
            "model": "gpt-3.5-turbo-0613",
            "object": "chat.completion",
            "usage": {
                "completion_tokens": 17,
                "prompt_tokens": 57,
                "total_tokens": 74
            }
        }
        """

        # Returning the assistant's analysis
        return response


# Usage:
# openai key : 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
if __name__ == "__main__":
    assistant = ChatGPTReviewAnalyzer(key = "sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV")
    current_path = os.path.dirname(os.path.abspath(__file__))
    result = assistant.analyze_batch_reviews_from_file(f"{current_path}/EcoSmart 100-Watt Equivalent Smart A21 Color Changing CEC LED Light Bulb with Voice Control (1-Bulb) Powered by Hubspace 11A21100WRGBWH1 - The Home Depot.txt")
    print(result)
