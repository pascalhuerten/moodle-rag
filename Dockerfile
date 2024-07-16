# Use an official Python runtime as a parent image
ARG PYTHON_VERSION=3.10.13
FROM python:$PYTHON_VERSION

ENV PYTHONPATH=/code

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install pip --upgrade && pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# Make the host_port available to the world outside this container
EXPOSE 7680

# Run the FastAPI app when the container launches
CMD uvicorn src.app:app --host 0.0.0.0 --port 7680 --root-path $ROOT_PATH --reload