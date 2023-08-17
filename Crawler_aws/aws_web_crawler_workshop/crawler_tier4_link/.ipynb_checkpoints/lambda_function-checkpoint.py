import datetime
import os

import boto3
import botocore
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from crochet import setup
import json
import threading
from momocrawler.spiders.momoshop import MomoshopSpider

queue_tier2_links = os.getenv('QUEUE_TIER2_LINKS')
region = os.getenv('REGION')
sqs = boto3.client('sqs', region_name=region, config=botocore.client.Config(max_pool_connections=500))

# Initialize Crochet
setup()


class LambdaRunner:
    target_url = ""
    receipt_handle = ""
    timeout = False
    input_url = ""

    def __init__(self, url):
        self.finished = threading.Event()
        self.results = []
        if url != "":
            self.target_url = url

    def run_spider(self):
        # Create a CrawlerRunner with project settings
        settings = get_project_settings()
        runner = CrawlerRunner(settings)

        # Create an instance of the spider class
        spider_cls = MomoshopSpider

        # Callback function to handle the spider results
        def handle_results(result):
            self.results.append(result)

            # Check if the spider has finished running
            if len(self.results) == 1:
                self.finished.set()

        # self.target_url = self.get_tier2_url_from_sqs()
        # self.delete_tier2_url_from_sqs()

        print(f'input_url:{self.input_url}; target_url:{self.target_url}')

        # Start the first spider run
        deferred = runner.crawl(spider_cls, url=self.target_url, runner=self)
        deferred.addCallback(handle_results)

        # Start the reactor
        runner.join()

    def delete_tier2_url_from_sqs(self):
        # Delete the message from the queue
        print("Deleting queue_tier2_links from start_requests")
        try:
            sqs.delete_message(
                QueueUrl=queue_tier2_links,
                ReceiptHandle=self.receipt_handle
            )
        except Exception as e:
            print(str(e))
        print("queue_tier2_links has been deleted.")

    # def get_tier2_url_from_sqs(self):
    #     if self.target_url == "":
    #         response = sqs.receive_message(
    #             QueueUrl=queue_tier2_links,
    #             MaxNumberOfMessages=1,  # Retrieve only one message
    #             WaitTimeSeconds=0  # Maximum time to wait for messages (long polling)
    #         )
    #
    #         # Process the received message if available
    #         messages = response.get('Messages', [])
    #         if messages:
    #             message = messages[0]
    #             self.target_url = message['Body']
    #             self.receipt_handle = message['ReceiptHandle']
    #             # Process the message body as needed
    #             print(f"Received message: {self.target_url}")
    #         else:
    #             msg = "All consumed."
    #             print(msg)
    #             self.target_url = ""
    #             return msg
    #
    #     return self.target_url

    def wait_for_completion(self):
        self.finished.wait()

    def get_results(self):
        return self.results


def handler(event, context):
    try:
        print("Starting to crawl")
        times = 0
        if "statusCode" not in event:
            # headers = {"Content-Type": "application/x-www-form-urlencoded",
            #            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}
            # response = requests.get('https://myip.com.tw/', headers=headers)
            #
            # # Check the response status code
            # if response.status_code == 200:
            #     ip = response.text[response.text.find("<font color=green>") + 18:response.text.find("</font></h1>")]
            #     # Request was successful
            #     print(ip)
            # else:
            #     # Request failed
            #     print('Request failed with status code:', response.status_code)
            runner = LambdaRunner(event["category_link"])
            runner.input_url = event["category_link"]
            runner.run_spider()
            runner.wait_for_completion()
            print(f"End date and time:{datetime.datetime.now()}")

        else:
            times = int(event["times"])
            if times < 3:
                runner = LambdaRunner(event["category_link"])
                runner.input_url = event["category_link"]
                runner.run_spider()
                runner.wait_for_completion()
                print(f"End date and time:{datetime.datetime.now()}")
            else:
                return {
                    'statusCode': 429,
                    'body': "",
                    'times': times,
                    "category_link": event["category_link"]
                }

        times = times + 1
        if not runner.timeout:
            return {
                'statusCode': 200,
                'body': 'Completed!',
                'times': times,
                "category_link": event["category_link"]
            }
        else:
            return {
                'statusCode': 408,
                'body': event["category_link"],
                'times': times,
                "category_link": event["category_link"]
            }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
#
#
# if __name__ == '__main__':
#     handler("", "")
if __name__ == '__main__':
    handler({'category_link': 'https://www.momoshop.com.tw/category/MgrpCategory.jsp?m_code=4801500006&mdiv=1099700000-bt_0_997_20-bt_0_997_20_P104_11_e1&ctype=B', 'body': 'https://www.momoshop.com.tw/'}, "")

