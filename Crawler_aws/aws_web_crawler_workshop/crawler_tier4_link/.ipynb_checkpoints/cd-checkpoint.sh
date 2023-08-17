aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 407620147666.dkr.ecr.ap-northeast-1.amazonaws.com
docker build -t aws_crawler_tier4_link .
docker tag aws_crawler_tier4_link:latest 407620147666.dkr.ecr.ap-northeast-1.amazonaws.com/aws_crawler_tier4_link:latest
docker push 407620147666.dkr.ecr.ap-northeast-1.amazonaws.com/aws_crawler_tier4_link:latest
