from GPT_interface import GPTInterface
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

system_info_overall = """You will analyze customer reviews and organize the findings into a JSON structured format with 5 key sections. The sections are:

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
    ```
"""


system_info_negative = """You will be presented with negative part of customer reviews and your job is to identify and list the most frequently mentioned negative aspects and issues of the product, along with the count of unique reviews mentioning each con. organize the findings into a JSON structured format, here is an example format for output:
```
{
    "Connectivity issues": {
      "description": "Problems with maintaining a stable connection, frequent disconnects, and difficulties in pairing the device.",
      "count": 28
    },
    "Limited outdoor functionality": {
      "description": "The product does not perform well in outdoor environments or is not designed to be used outdoors.",
      "count": 23
    },
    "Occasional humming noise at high brightness": {
      "description": "A noticeable humming or buzzing sound occurs when the product is set to high brightness levels.",
      "count": 15
    },
    "App requires frequent logins": {
      "description": "The associated app frequently logs users out, requiring them to log back in often.",
      "count": 12
    },
    "Inconsistent response time": {
      "description": "The product has delays or lag in responding to commands or changes in settings.",
      "count": 4
    },
    "Wi-Fi connection drops": {
      "description": "The device often loses its Wi-Fi connection, causing interruptions in usage.",
      "count": 38
    },
    "Bulb longevity": {
      "description": "The lifespan of the bulb is shorter than expected or advertised.",
      "count": 6
    },
    "App performance": {
      "description": "General performance issues with the app, including crashes, slow load times, and unresponsiveness.",
      "count": 5
    },
    "Compatibility with certain light fixtures": {
      "description": "The product is not compatible with some types of light fixtures or setups.",
      "count": 4
    },
    "Color brightness not as expected": {
      "description": "The brightness of the colors does not meet user expectations or advertised levels.",
      "count": 3
    }
  }
```

"""


system_prompt_summary = """
    summarize several batch analysis results of customer reivews into final result and output json, the ouput format must keep the same as the input format.
"""

BATCHSIZE = 220

class GPTReviewsAnalyzer():
    def __init__(self,key,host):
        self.gpt_client = GPTInterface(key, host)
    
    def analyze_batch_reviews_from_file(self, filepath: str, type = None, prompt = None, product_name = None) -> str:
        with open(filepath, 'r',encoding='utf-8') as file:
            reviews = file.readlines()

        # Combine all reviews into one string for processing
        combined_reviews = " ".join(reviews)
        return self.analyze_reviews(combined_reviews, type = type, prompt = prompt, product_name = product_name)

    def split_and_analyze_reviews_file(self, file_path, type = None, prompt = None, product_name = None) -> str:
        ret = []
        batch_size = BATCHSIZE
        batches = self.split_reviews_file(file_path, batch_size)
        MAX_RETRIES = 2

        def execute_analysis(batch, retries=0):
            logging.info(f"Start to analyze batch -----------------\n")
            result = self.analyze_reviews(batch, type, prompt, product_name)
            if result["status"] is True or retries >= MAX_RETRIES:
                return result
            else:
                print(f"Retrying Batch Analysis. Attempt: {retries + 1}")
                return execute_analysis(batch, retries + 1)

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_batch = {executor.submit(execute_analysis, batch): batch for batch in batches}
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    result = future.result()
                    if result["status"] is True:
                        ret.append(result)
                    else:
                        # Log the final failure after retries
                        print(f"Final failure in analyzing batch after {MAX_RETRIES} retries.")
                        return {
                                    "status": False,
                                    "message": f"batch analysis fail",
                                    "data": None
                                }
                except Exception as exc:
                    print(f'Batch generated an exception: {exc}')
                    return {
                                    "status": False,
                                    "message": f"batch analysis fail",
                                    "data": None
                                }

        # for i, batch in enumerate(batches, 1):
        #     print(f"Start to analyze Batch {i}:\n")
        #     retry = 0
        #     while retry < 2:
        #         result = self.analyze_reviews(batch, type = type, prompt = prompt, product_name = product_name)
        #         if result["status"] is True:
        #             ret.append(result)
        #             break
        #         else:
        #             retry += 1
        #             print(f"fail to get result, retry {retry}:\n")
        #             if retry == 2:
        #                 print(f"fail to get result for batch {i}\n")
        #                 return {
        #                             "status": False,
        #                             "message": f"batch {i} analysis fail",
        #                             "data": None
        #                         }

        # FIXME : get the ret and then summarize all anslysis_result with GPT

        if len(ret) < 2:
            logging.info(ret[0])
            return ret[0]

        analysis_result_list = []
        ret_result = {
            "status": True,
            "message": "Analysis completed successfully",
            "data": {
                "analysis_result": None,  # The main analysis result
                # Metadata integrated into data
                "metadata": {
                    "model": model if 'model' in locals() else None,
                    "finish_reason": finish_reason if 'finish_reason' in locals() else None,
                    "token_input": 0,
                    "token_output": 0,
                    # Any other metadata details
                }
                # Include other relevant data here if necessary
            }
        }
        for i, ret_i in enumerate(ret, 1):
            logging.info(f"get result for Batch {i}:\n")
            logging.info(ret_i)
            analysis_result_list.append(ret_i["data"]["analysis_result"])
            ret_result["data"]["metadata"]["token_input"]+=ret_i["data"]["metadata"]["token_input"]
            ret_result["data"]["metadata"]["token_output"]+=ret_i["data"]["metadata"]["token_output"]
            
        summary_ret = self.summarize_analysis_result(analysis_result_list, product_name=product_name)
        logging.info(f"get result for summary:\n")
        logging.info(summary_ret)
        summary_ret["data"]["metadata"]["token_input"]+=ret_result["data"]["metadata"]["token_input"]
        summary_ret["data"]["metadata"]["token_output"]+=ret_result["data"]["metadata"]["token_output"]

        return summary_ret
    
    def analyze_reviews(self, reviews: str, type = None, prompt = None, product_name = None) -> str:
        if prompt is None:
            if type == 'negative':
                system_prompt = system_info_negative
            else:
                system_prompt = system_info_overall
        else:
            system_prompt = prompt
        if product_name is not None:
            pre_user_prompt = f"The following are the customer views for product <{product_name}>: \n\n"
        else:
            pre_user_prompt = f"The following are the customer views: \n\n"

        user_prompt = f"{pre_user_prompt}```{reviews}```"

        token_num = self.gpt_client.count_token(user_prompt, 'gpt-4')
        logging.info(f"token_num:{token_num}")

        if token_num > 120000:
            logging.error(f"too large context")
            result = {
                "status": False,
                "message": "Too large context",
                "data": None
            }
            return result
        
        ret = self.gpt_client.chat(model_name= None, system_prompt = system_prompt, user_prompt = user_prompt, assistant_prompt = None)
        if ret["status"] is False:
            return {
                "status": False,
                "message": ret["message"],
                "data": None
            }
        
        chat_reply = ret["data"]

        # Returning the assistant's analysis
        if chat_reply.choices[0].message.content:
            response = chat_reply.choices[0].message.content
            logging.debug(response)
            '''
            # Remove '\n'
            response = response.replace('\n', '')

            # Remove '%'
            response = response.replace('%', '')

            # Remove '\\n\\n'
            response = response.replace('\\n\\n', '')
            '''

        if chat_reply.model:
            model = chat_reply.model
        else:
            model =None

        if chat_reply.choices[0].finish_reason:
            finish_reason = chat_reply.choices[0].finish_reason
        else:
            finish_reason = None
            
        
        if chat_reply.usage:
            token_input = chat_reply.usage.prompt_tokens
            token_output = chat_reply.usage.completion_tokens
        else:
            token_input = 0
            token_output = 0

            # Assuming response and other variables are set correctly
        result = {
            "status": True,
            "message": "Analysis completed successfully",
            "data": {
                "analysis_result": response,  # The main analysis result
                # Metadata integrated into data
                "metadata": {
                    "model": model if 'model' in locals() else None,
                    "finish_reason": finish_reason if 'finish_reason' in locals() else None,
                    "token_input": token_input if 'token_input' in locals() else 0,
                    "token_output": token_output if 'token_output' in locals() else 0,
                    # Any other metadata details
                }
                # Include other relevant data here if necessary
            }
        }

        return result
    
    def summarize_analysis_result(self, analysis_result_list: list, prompt = None, product_name = None) -> str:
        if prompt is None:
            system_prompt = system_prompt_summary
        else:
            system_prompt = prompt
        if product_name is not None:
            pre_user_prompt = f"The following is a list analysis reuslt for product <{product_name}>, the number means the happend times of the item, please combine similar items and accumulate the times : \n\n"
        else:
            pre_user_prompt = f"The following is a list analysis reuslt for a product, the number means the happend times of the item, please combine similar items and accumulate the times: \n\n"

        user_prompt = f"{pre_user_prompt}```{str(analysis_result_list)}```"

        token_num = self.gpt_client.count_token(user_prompt, 'gpt-4')
        logging.debug(f"token_num:{token_num}")

        if token_num > 120000:
            logging.error(f"too large context")
            result = {
                "status": False,
                "message": "Too large context",
                "data": None
            }
            return result
        
        ret = self.gpt_client.chat(model_name= None, system_prompt = system_prompt, user_prompt = user_prompt, assistant_prompt = None, max_output_tokens= 2048)
        if ret is False:
            return {
                "status": False,
                "message": ret["message"],
                "data": None
            }

        chat_reply = ret["data"]

        # Returning the assistant's analysis
        if chat_reply.choices[0].message.content:
            response = chat_reply.choices[0].message.content
            logging.debug(response)
            '''
            # Remove '\n'
            response = response.replace('\n', '')

            # Remove '%'
            response = response.replace('%', '')

            # Remove '\\n\\n'
            response = response.replace('\\n\\n', '')
            '''

        if chat_reply.model:
            model = chat_reply.model
        else:
            model =None

        if chat_reply.choices[0].finish_reason:
            finish_reason = chat_reply.choices[0].finish_reason
        else:
            finish_reason = None
            
        
        if chat_reply.usage:
            token_input = chat_reply.usage.prompt_tokens
            token_output = chat_reply.usage.completion_tokens
        else:
            token_input = 0
            token_output = 0

            # Assuming response and other variables are set correctly
        result = {
            "status": True,
            "message": "Analysis completed successfully",
            "data": {
                "analysis_result": response,  # The main analysis result
                # Metadata integrated into data
                "metadata": {
                    "model": model if 'model' in locals() else None,
                    "finish_reason": finish_reason if 'finish_reason' in locals() else None,
                    "token_input": token_input if 'token_input' in locals() else 0,
                    "token_output": token_output if 'token_output' in locals() else 0,
                    # Any other metadata details
                }
                # Include other relevant data here if necessary
            }
        }

        return result

    
    """
    Reads content from a file and splits it into batches using article_split.

    :param file_path: Path to the file containing the article.
    :param batch_size: The number of reviews per batch.
    :return: A list of batches, each batch containing several reviews.
    """
    def split_reviews_file(self,file_path, batch_size):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                batches = self.article_split(content, batch_size)
                # Debugging information
                total_reviews = len(content.strip().split('\nDate:'))
                print(f"Total number of reviews: {total_reviews}")
                print(f"Total number of batches: {len(batches)}")

                for i, batch in enumerate(batches, 1):
                    num_reviews_in_batch = len(batch.strip().split('\nDate:'))
                    print(f"Batch {i} has {num_reviews_in_batch} review(s):\n\n")
                return batches
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def split_algorithm(self,num_items, batch_size):
        num_batches = -(-num_items // batch_size)  # Ceiling division
        optimal_batch_size = num_items // num_batches
        remainder = num_items % num_batches

        batches = []
        start_index = 0

        for _ in range(num_batches):
            additional_size = 1 if remainder > 0 else 0
            end_index = start_index + optimal_batch_size + additional_size - 1
            batches.append((start_index, end_index))
            start_index = end_index + 1
            remainder -= 1

        return batches

    def article_split(self, context:str, batch_size) -> list:
        # Ensure the string starts with "Date:" for consistent splitting
        if not context.startswith("Date:"):
            context = "Date:" + context

        # Split the context into individual reviews, using "\nDate:" as the separator
        reviews = context.strip().split('\nDate:')

        # Adjust for the empty first element if it exists
        if reviews[0] == '':
            reviews = reviews[1:]

        # Prepend "Date:" to each review except the first one
        reviews = [reviews[0]] + ["Date:" + review for review in reviews[1:]]

        # Calculate the batch indices
        batch_indices = self.split_algorithm(len(reviews), batch_size)

        # Split the reviews into batches
        batched_reviews = []
        for start_idx, end_idx in batch_indices:
            batch = '\n'.join(reviews[start_idx:end_idx + 1])
            batched_reviews.append(batch)

        return batched_reviews

    def article_split_by_word_count(self, context, target_word_count):
        # Split the context into individual reviews
        reviews = context.strip().split('\nDate:')
        if reviews[0] == '':
            reviews = reviews[1:]
        reviews = ['Date:' + review for review in reviews]

        batches = []
        current_batch = []
        current_word_count = 0

        for review in reviews:
            review_word_count = len(review.split())

            if current_batch and current_word_count + review_word_count > target_word_count:
                batches.append('\n'.join(current_batch))
                current_batch = [review]
                current_word_count = review_word_count
            else:
                current_batch.append(review)
                current_word_count += review_word_count

        if current_batch:
            batches.append('\n'.join(current_batch))

        return batches

    def process_file_by_word_count(self, file_path, batch_size):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Use article_split_by_word_count to split into batches
            batches = self.article_split_by_word_count(content, batch_size)

            # Debugging information
            total_reviews = len(content.strip().split('\nDate:'))
            print(f"Total number of reviews: {total_reviews}")
            print(f"Total number of batches: {len(batches)}")

            for i, batch in enumerate(batches, 1):
                batch_word_count = sum(len(review.split()) for review in batch.split('\n'))
                print(f"Batch {i} (word count: {batch_word_count}):")
                print(batch)
                print()

            return batches

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return []


if __name__ == '__main__':
    # batch_size = 69
    analyzer = GPTReviewsAnalyzer(key="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", host= "remote3")
    # batches = analyzer.split_reviews_file('C:/Users/d87wvh/THD_VOC_Bot/Hampton Bay Fanelee 54 in. White Color Changing LED Brushed Nickel Smart Ceiling Fan with Light Kit and Remote Powered by Hubspace 52133 - The Home Depot.txt', batch_size)
    # for i, batch in enumerate(batches, 1):
    #     print(f"Batch {i}:\n{batch}\n")
    logging.info("start split_and_analyze_reviews_file")
    result = analyzer.split_and_analyze_reviews_file("/home/lighthouse/server/THD_VOC_Bot_Temp/Hampton Bay Fanelee 54 in. White Color Changing LED Brushed Nickel Smart Ceiling Fan with Light Kit and Remote Powered by Hubspace 52133 - The Home Depot.txt", product_name='Hampton Bay Fanelee 54 in. White Color Changing LED Brushed Nickel Smart Ceiling Fan with Light Kit and Remote Powered by Hubspace 52133')
    logging.info(f"result: {result}")



