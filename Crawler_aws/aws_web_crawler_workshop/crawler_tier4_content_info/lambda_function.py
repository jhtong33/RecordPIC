import datetime
import json
import os
from fake_useragent import UserAgent
import boto3
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from crochet import setup
import threading
from momocrawler.spiders.momoshop import MomoshopSpider

# Initialize Crochet
setup()

ua = UserAgent()
region = os.getenv('REGION')
sqs = boto3.client('sqs', region_name=region)
queue_tier4_content_links = os.getenv('QUEUE_TIER4_CONTENT_LINKS')


class LambdaRunner:
    target_url = ""
    receipt_handle = ""
    tier4_content_object = None
    timeout = False

    def __init__(self, url):
        self.finished = threading.Event()
        self.results = []
        if url != "":
            self.target_url = url

    def run_spider(self):
        # Create a CrawlerRunner with project settings
        settings = get_project_settings()
        runner = CrawlerRunner(settings)
        if self.target_url == "":
            self.get_tier4_content_url_from_sqs()

        # Callback function to handle the spider results
        def handle_results(result):
            self.results.append(result)

            # Check if the spider has finished running
            if len(self.results) == 1:
                self.finished.set()

        # Start the first spider run
        deferred = runner.crawl(MomoshopSpider, self)
        deferred.addCallback(handle_results)

        # Start the reactor
        runner.join()

    def wait_for_completion(self):
        self.finished.wait()

    def get_results(self):
        return self.results

    def get_tier4_content_url_from_sqs(self):
        response = sqs.receive_message(
            QueueUrl=queue_tier4_content_links,
            MaxNumberOfMessages=1,  # Retrieve 1 messages
            WaitTimeSeconds=0  # Maximum time to wait for messages (long polling)
        )
        messages = response.get('Messages', [])
        if messages is not None:
            self.tier4_content_object = messages[0]
        else:
            msg = "All consumed."
            print(msg)
            return msg

        # Delete messages from SQS
        for message in messages:
            sqs.delete_message(
                QueueUrl=queue_tier4_content_links,
                ReceiptHandle=message['ReceiptHandle']
            )


def handler(event, context):
    try:
        # Check if the function was triggered by an HTTP request or Lambda event
        # print(f"Starting to crawl:{datetime.datetime.now()}")
        times = 0
        if "statusCode" not in event:
            # If the function was not triggered by retry
            runner = LambdaRunner("")
            runner.run_spider()
            runner.wait_for_completion()
            # print(f"End date and time:{datetime.datetime.now()}")
        else:
            times = int(event["times"])
            if times < 4:
                runner = LambdaRunner(event["tier4_content_link"])
                runner.input_url = event["tier4_content_link"]
                runner.run_spider()
                runner.wait_for_completion()
                # print(f"End date and time:{datetime.datetime.now()}")
            else:
                print(f'Retry too many times, 429:{event["tier4_content_link"]}')
                # If the retry count is 4 or more, return an HTTP 429 response indicating Too Many Requests
                return {
                    'statusCode': 429,
                    'body': "",
                    'times': times,
                    "tier4_content_link": event["tier4_content_link"]
                }

        times = times + 1
        if not runner.timeout:
            # print("success")
            # If the LambdaRunner completed successfully, return an HTTP 200 response with the completion details
            return {
                'statusCode': 200
                # 'body': 'Completed!',
                # 'times': times
            }
        else:
            # print('timeout')
            # If the LambdaRunner timed out, return an HTTP 408 response with the category objects
            return {
                'statusCode': 408,
                'times': times,
                "tier4_content_link": json.loads(runner.tier4_content_object['Body'])['tier4_content_link']
            }
    except Exception as e:
        print(f'fail:{e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

#
if __name__ == '__main__':
    handler({'statusCode': 408,'times':1, 'tier4_content_link': 'https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=10242320&str_category_code=2919100975&sourcePageType=4'}, "")
