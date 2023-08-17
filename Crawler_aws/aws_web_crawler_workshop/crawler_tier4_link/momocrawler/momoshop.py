import hashlib
import json
import threading
import scrapy
from fake_useragent import UserAgent
from scrapy_selenium import SeleniumRequest
import logging
import os
import boto3
import botocore

ua = UserAgent()
region = os.getenv('REGION')
sqs = boto3.client('sqs', region_name=region, config=botocore.client.Config(max_pool_connections=500))
s3 = boto3.client('s3', region_name=region, config=botocore.client.Config(max_pool_connections=500))
queue_tier2_links = os.getenv('QUEUE_TIER2_LINKS')
queue_tier4_links = os.getenv('QUEUE_TIER4_LINKS')
s3_bucket_name = os.getenv('S3_BUCKET_NAME')
export_to_s3 = os.getenv('EXPORT_TO_S3')


def check_tier(tier_dict: dict):
    if "tier4" in tier_dict:
        return "tier4"
    elif "tier3" in tier_dict:
        return "tier3"
    elif "tier2" in tier_dict:
        return "tier2"
    else:
        return "tier1"


def hash_function(original_string):
    # Create a hash object using SHA-256 algorithm
    hasher = hashlib.sha256()

    # Convert the input string to bytes (required by hashlib)
    input_bytes = original_string.encode('utf-8')

    # Update the hash object with the input bytes
    hasher.update(input_bytes)

    # Get the hexadecimal representation of the hash value
    return hasher.hexdigest()


class MomoshopSpider(scrapy.Spider):
    name = "momoshop"
    allowed_domains = ["www.momoshop.com.tw"]
    user_agent = ua.random
    receipt_handle = None

    def start_requests(self):
        print("Starting queue_tier2_links from start_requests")
        response = sqs.receive_message(
            QueueUrl=queue_tier2_links,
            MaxNumberOfMessages=1,  # Retrieve only one message
            WaitTimeSeconds=5  # Maximum time to wait for messages (long polling)
        )

        # Process the received message if available
        messages = response.get('Messages', [])
        if messages:
            message = messages[0]
            message_body = message['Body']
            self.receipt_handle = message['ReceiptHandle']

            # Process the message body as needed
            print(f"Received message: {message_body}")
            yield SeleniumRequest(url=message_body, callback=self.parse_tier2)

        else:
            msg = "All consumed."
            print(msg)
            return msg

    @staticmethod
    def send_to_sqs(message):
        try:
            print(message['MessageGroupId'])
            response = sqs.send_message(QueueUrl=queue_tier4_links,
                                        MessageGroupId=message['MessageGroupId'],
                                        MessageBody=message['MessageBody'],
                                        MessageDeduplicationId=message['MessageGroupId'])
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                print('Fail')
        except Exception as e:
            print(str(e))

    @staticmethod
    def send_to_s3(m, hash_id):
        try:
            json_file_name = f'{hash_id}.json'
            response = s3.put_object(Bucket=s3_bucket_name, Key=json_file_name, Body=json.dumps(m, ensure_ascii=False))
            # check if it's successful
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                print('Fail')
        except Exception as e:
            print(str(e))

    def parse_tier2(self, response):
        try:
            print("Starting to parse_tier2")
            categories = response.css('#bt_category_Content ul li')
            tier_dict = {}
            threads = []
            if len(categories) > 0:
                tier_path = response.css("#bt_2_layout_NAV ul li")
                tier_index = 1
                for tier in tier_path:
                    if tier.css("::attr(class)").get() != 'first':
                        tier_a = tier.css("a").get()
                        if tier_a is not None:
                            tier_dict[f'tier{tier_index}'] = tier.css("a::text").get()
                        else:
                            tier_dict[f'tier{tier_index}'] = tier.css("::text").get()
                        tier_index = tier_index+1
            if "tier1" in tier_dict:

                for category in categories:
                    class_name = category.css('::attr(class)').get()
                    category_item_a = category.css('a').get()
                    if category_item_a is not None and str(class_name).find("cateMLink") == -1:
                        tier_dict['tier4'] = category.css("a::text").get()
                        category_link = category.css('li a::attr(href)').get()
                    else:
                        tier_dict['tier3'] = category.css("a::text").get()
                        category_link = category.css('li a::attr(href)').get() if not None else ""

                    category_link = "https://www.momoshop.com.tw" + category_link
                    # Generate a unique Id using the current timestamp and a UUID
                    # message_id = f"{int(time.time())}-{str(uuid.uuid4())}"
                    message_body = {'tier1_category_name': tier_dict["tier1"],
                                    'tier2_category_name': tier_dict.get("tier2", ""),
                                    'tier3_category_name': tier_dict.get("tier3", ""),
                                    'tier4_category_name': tier_dict.get("tier4", ""),
                                    'category_link': category_link if category_link.find("javascript") == -1 else "",
                                    'category_type': check_tier(tier_dict)}
                    hash_id = hash_function(str(message_body))
                    message = {'Id': hash_id, 'MessageGroupId': hash_id,
                                              'MessageBody': json.dumps({
                                               'tier1_category_name': tier_dict["tier1"],
                                               'tier2_category_name': tier_dict.get("tier2", ""),
                                               'tier3_category_name': tier_dict.get("tier3", ""),
                                               'tier4_category_name': tier_dict.get("tier4", ""),
                                               'category_link': category_link if category_link.find("javascript") == -1 else "",
                                               'category_type': check_tier(tier_dict)}, ensure_ascii=False)}

                    thread_sqs = threading.Thread(target=self.send_to_sqs, args=(message,))
                    threads.append(thread_sqs)
                    thread_sqs.start()

                    # self.send_to_sqs(message)
                    if export_to_s3 is not None and export_to_s3 == "On":
                        thread_s3 = threading.Thread(target=self.send_to_s3, args=(message_body, hash_id))
                        threads.append(thread_s3)
                        thread_s3.start()
                        self.send_to_s3(message_body, hash_id)

                for thread in threads:
                    thread.join()

        except Exception as e:
            logging.error(e)
        finally:
            # Delete the message from the queue
            print("Deleting queue_tier2_links from start_requests")
            sqs.delete_message(
                QueueUrl=queue_tier2_links,
                ReceiptHandle=self.receipt_handle
            )
            print("queue_tier2_links has been deleted.")
