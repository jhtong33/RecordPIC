aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 407620147666.dkr.ecr.ap-northeast-1.amazonaws.com
docker build -t  pic_iopenmall_crawler_tier5_link .
docker tag pic_iopenmall_crawler_tier5_link:latest 407620147666.dkr.ecr.ap-northeast-1.amazonaws.com/pic_iopenmall_crawler_tier5_link:latest
docker push 407620147666.dkr.ecr.ap-northeast-1.amazonaws.com/pic_iopenmall_crawler_tier5_link:latest
