import datetime
import os
import boto3
import botocore
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from crochet import setup
import json
import threading
rom openmallcrawler.spiders.iopenmall import IOpenmallSpider

# Retrieve environment variables
queue_tier2_links = os.getenv('QUEUE_TIER2_LINKS')
region = os.getenv('REGION')
sqs = boto3.client('sqs', region_name=region, config=botocore.client.Config(max_pool_connections=500))
timeout_seconds = float(os.getenv('TIMEOUT')) if os.getenv('TIMEOUT') is not None else 150  # seconds
# Initialize Crochet
setup()


# Class for running the Lambda spider
class LambdaRunner_2:
    target_url = ""
    receipt_handle = ""
    timeout = True
    input_url = ""
    category_info = []
    
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
        spider_cls = IOpenMall

        # Callback function to handle the spider results
        def handle_results(result):
            self.results.append(result)

            # Check if the spider has finished running
            if len(self.results) == 1:
                self.finished.set()

        # Start the first spider run
        deferred = runner.crawl(spider_cls, url=self.target_url, runner=self)
        deferred.addCallback(handle_results)

        # Start the reactor
        runner.join()

    # Function to wait for spider completion
    def wait_for_completion(self):
        self.finished.wait(timeout=timeout_seconds)

    # Function to get spider results
    def get_results(self):
        return self.results


# Main handler function for the Lambda
def handler(event, context):
    try:
        print(f"Starting to crawl: {datetime.datetime.now()}")
        times = 0
        if "statusCode" not in event:
            # Initialize the LambdaRunner with the provided category link

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
            runner = LambdaRunner_2(event["category_link"])
            runner.input_url = event["category_link"]
            runner.run_spider()
            runner.wait_for_completion()

            print(f"End date and time:{datetime.datetime.now()}")

        else:
            times = int(event["times"])
            if times < 4:
                # Initialize the LambdaRunner with the provided category link
                runner = LambdaRunner_2(event["category_link"])
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
                # "category_link": event["category_link"],
                # "category_info": runner.category_info
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
    
    
if __name__ == '__main__':
    handler({'category_link': '', 'body': ''}, "")

