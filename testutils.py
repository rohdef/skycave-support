import json
import socket
import logging

class TestError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def test_response(logger, response, reply, tail):
    try:
        res = json.loads(response.decode("utf-8"))
        reply_tail = []
        if 'reply-tail' in res:
            reply_tail = res['reply-tail']

        error_code = res['error-code']
        if error_code != "OK":
            logger.error("Error in validating error code in the response")
            logger.error("Expected the error code: OK")
            logger.error("Actual error code was: %s", error_code)
            logger.error("The complete output was: %s", response)
            raise TestError('Test failed')

        json_reply = res['reply']
        if not reply in json_reply:
            logger.error("Error in validating the reply part of the response")
            logger.error("Expected the reply to contain: %s", reply)
            logger.error("The actual reply was: %s", json_reply)
            logger.error("The complete output was: %s", response)
            raise TestError('Test failed')

        for x in tail:
            if x not in reply_tail:
                logger.error("Error in validating the tail part part of the response")
                logger.error("Expected the tail to contain: %s", x)
                logger.error("The tail was: %s", str(reply_tail))
                logger.error("The complete output was: %s", response)
                raise TestError('Test failed')
    except TestError:
        raise TestError("Test failed")
    except:
        raise

def test_error_response(logger, response, code, message):
    try:
        res = json.loads(response.decode("utf-8"))

        error_code = res['error-code']
        if not code in error_code:
            logger.error("Error in the expected error code")
            logger.error("Expected code was: %s", code)
            logger.error("Actual code was: %s", error_code)
            logger.error("Complete response %s", response)
            raise TestError('Test failed')

        error_message = res['error-message']
        if not message.upper() in error_message.upper():
            logger.error("Unexpected error message in the error response")
            logger.error("Expected to contain: %s", message)
            logger.error("Actual message was: %s", error_message)
            logger.error("Complete json is: %s", response)
            raise TestError('Test failed')

    except TestError:
        raise TestError("Test failed")
    except:
        raise

def lstr(*items):
    return str(list(items)).replace("'", '"')

class RabbitSocket():
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self.channel = connection.channel()

        result = channel.queue_declare()
        self.callback_queue = result.method.queue
        self.channel.basic_consume(self.on_response,
                                   no_ack=True,
                                   queue=self.callback_queue)

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def send(bytes):
        self.response = None
        self.corr_id = str(uuid.uuid4())

        self.channel.basic_publish(exchange='',
                                   routing_key='rpc_queue',
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue,
                                       correlation_id = self.corr_id
                                   ),
                                   body=bytes.encode("UTF-8"))
        pass

    def recv(ignore_this):
        while self.response == None:
            self.connection.process_data_events()
        return self.response

    def close(self):
        self.connection.close()

class TestRunner:
    def __init__(self, handler, host, port, useRabbit=False):
        self.useRabbit = useRabbit
        self.host = host
        self.port = port

        self.testTotal = 0
        self.successTotal = 0
        self.failureTotal = 0
        self.errorTotal = 0

        self.logger = logging.getLogger("Test Runner")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def runTest(self, test):
        try:
            self.logger.info("running a test")
            self.testTotal += 1

            if self.useRabbit:
                self.logger.info("running with RabbitMQ")
                rabbit_handle(test)
            else:
                self.logger.info("running with socket")
                self.sock_handle(test)

            self.successTotal += 1
        except TestError:
            self.logger.info("Caught a test error")
            self.failureTotal += 1
        except:
            logging.exception("Error during running the test")
            self.errorTotal += 1

    def get_test_tuple(self):
        return (self.testTotal, self.successTotal, self.failureTotal, self.errorTotal)

    def sock_handle(self, test):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.host, self.port))
        test(client_socket)
        client_socket.close()

    def rabbit_handle(self, test):
        client_socket = RabbitSocket(self.host, self.port)
        test(client_socket)
