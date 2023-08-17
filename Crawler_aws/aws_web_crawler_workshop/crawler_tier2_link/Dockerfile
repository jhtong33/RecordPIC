#ARG FUNCTION_DIR="/src"
# Use Python 3.9.17 as the base image
FROM public.ecr.aws/lambda/python@sha256:10dbb67ede15b5fd516be87dd71c3f7968904b0b840235720486476b34ef9b67
RUN yum install atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel -y

# Set environment variables
# Set the timezone
ENV TZ=Asia/Taipei
# Set the working directory inside the container
COPY requirements.txt ${LAMBDA_TASK_ROOT}
# Install requirements
RUN pip install -r requirements.txt


# Copy the contents of the current directory to the working directory in the container
COPY momocrawler ${LAMBDA_TASK_ROOT}/momocrawler
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY scrapy.cfg ${LAMBDA_TASK_ROOT}
CMD [ "lambda_function.handler" ]