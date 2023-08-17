import hashlib
import os
import threading

import botocore
import scrapy
from fake_useragent import UserAgent
import boto3

ua = UserAgent()
region = os.getenv('REGION')
sqs = boto3.client('sqs', region_name=region, config=botocore.client.Config(max_pool_connections=50))
queue_tier2_links = os.getenv('QUEUE_TIER2_LINKS')
region = os.getenv('REGION')


class MomoshopSpider(scrapy.Spider):
    name = "momoshop"
    allowed_domains = ["www.momoshop.com.tw"]
    start_urls = ["https://www.momoshop.com.tw/main/Main.jsp"]
    user_agent = ua.random
    runner = None
    category_links = []

    def __init__(self, runner=None, **kwargs):
        self.runner = runner
        super(MomoshopSpider, self).__init__(**kwargs)

    def parse(self, response, **kwargs):
        try:
            print("Starting to parse")
            sub_menus = response.css('.subMenu')
            for sub_menu in sub_menus:
                sub_menu_links = sub_menu.css("#topArea .dul .BTDME a::attr(href)")
                for sub_menu_link in sub_menu_links:
                    link = str(sub_menu_link.get())
                    if link.find("https") != -1 and link.find("category") != -1:
                        try:
                            self.category_links.append(link)

                        except Exception as e:
                            print(f'SeleniumRequest: error > {e}, link: {sub_menu_link.get()}')
            self.runner.category_links = self.category_links
            # self.send_category_links_to_sqs(self.category_links)
        except Exception as e:
            print(str(e))

#     @staticmethod
#     def send_to_sqs(message):
#         response = sqs.send_message(QueueUrl=queue_tier2_links, MessageGroupId=message['MessageGroupId'],
#                                     MessageBody=message['MessageBody'], MessageDeduplicationId=message['MessageGroupId'])
#         # check if it's successful
#         if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
#             print('Fail')
#
#     def send_category_links_to_sqs(self, links):
#         try:
#             print("Starting to send to SQS")
#             threads = []
#             for link in links:
#                 hash_id = hash_function(link)
#                 message = {'Id': hash_id, 'MessageGroupId': hash_id,
#                            'MessageBody': link}
#                 thread = threading.Thread(target=self.send_to_sqs, args=(message,))
#                 threads.append(thread)
#                 thread.start()
#
#             for thread in threads:
#                 thread.join()
#
#             # if messages:  # Check if there are any remaining messages in the list
#             #     self.send_to_sqs(messages)
#         except Exception as e:
#             print(str(e))
#
#
# def hash_function(original_string):
#     # Create a hash object using SHA-256 algorithm
#     hasher = hashlib.sha256()
#
#     # Convert the input string to bytes (required by hashlib)
#     input_bytes = original_string.encode('utf-8')
#
#     # Update the hash object with the input bytes
#     hasher.update(input_bytes)
#
#     # Get the hexadecimal representation of the hash value
#     return hasher.hexdigest()