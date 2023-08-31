import json
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from crochet import setup
import threading
from momocrawler.spiders.momoshop import MomoshopSpider

# Initialize Crochet
setup()


class LambdaRunner:
    category_links = []

    def __init__(self):
        self.finished = threading.Event()
        self.results = []

    def run_spider(self):
        # Create a CrawlerRunner with project settings
        settings = get_project_settings()
        runner = CrawlerRunner(settings)

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


def handler(event, context):
    try:
        print("Starting tier2 links crawling")
        runner = LambdaRunner()
        runner.run_spider()
        runner.wait_for_completion()

        queue_list = []

        # Aggregate input JSON format
        for category_link in runner.category_links:
            queue_list.append({'category_link': category_link})
        print(f'len(queue_list):{len(runner.category_links)}')
        print("success")
        return {
            'statusCode': 200,
            'body': {'message': queue_list}
        }
    except Exception as e:
        print(f'fail:{str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

#
if __name__ == '__main__':
    handler("", "")
