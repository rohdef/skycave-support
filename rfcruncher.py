import pika
import socket
import urllib
import json
import string
import traceback
import logging

######################################
#                                    #
#  CONFIGURATION                     #
#                                    #
######################################
host = "cave.smatso.dk"
#host = "localhost"
port = 37123
player_login = "20052356"
player_pass = "621985792"

######################################
#                                    #
# CACHE VARIABLES AND HELPERS        #
#                                    #
######################################
player_id = "ignore-player-id"
player_name = None
player_session = "ignore-session-id"

method_template = '{{"method":"{0}","parameter":"{1}","parameter-tail":{2},"player-id":"{3}","version":"2","player-session-id":"{4}"}}\n'

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
    except:
        raise TestError("Test failed")

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

    except:
        logging.exception("Error during error response handling")
        raise TestError("Test failed")
    
def sock_handle(fun):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    fun(client_socket)
    client_socket.close()

def lstr(*items):
    return str(list(items)).replace("'", '"')
    
def set_user_details(details):
    global player_id, player_name, player_session
    player_id = details[0]
    player_name = details[1]
    player_session = details[2]

def reset_user_details():
    global player_id, player_name, player_session
    player_id = "ignore-player-id"
    player_name = None
    player_session = "ignore-session-id"

def get_method_template(method, param, tail):
    req = method_template.format(method, param, tail, player_id, player_session)
    return bytes(req, "UTF-8")
    
def reset_server():
    def conn(client_socket):
        req = get_method_template("cave-login", player_login, lstr(player_pass))

        client_socket.send(req)
        response = client_socket.recv(4096)
        res = json.loads(response.decode("utf-8"))
        set_user_details(res['reply-tail'])
    sock_handle(conn)
        
    def dis_conn(client_socket):
        req = get_method_template("cave-logout", "", lstr())

        client_socket.send(req)
        response = client_socket.recv(4096)
        reset_user_details()
    sock_handle(dis_conn)

######################################
#                                    #
# TESTS                              #
#                                    #
######################################
class NicePeter():
    def __init__(self, handler):
        self.logger = logging.getLogger("Nice Peter")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        
    def test_login(self, client_socket):
        self.logger.info("Logging in")
        req = get_method_template("cave-login", player_login, lstr(player_pass))
        client_socket.send(req)

        response = client_socket.recv(4096)
        test_response(self.logger, response, "LOGIN_SUCCESS", ["55e45169e4b067dd3c8fa56e", "rohdef"])
        res = json.loads(response.decode("utf-8"))
        set_user_details(res['reply-tail'])
    

    def test_logout(self, client_socket):
        self.logger.info("Logging out")
        req = get_method_template("cave-logout", "", lstr())
        client_socket.send(req)

        response = client_socket.recv(4096)
        test_response(self.logger, response, "SUCCESS", [])

    def test_homecommand(self, client_socket):
        self.logger.info("Testing home command")
        req = get_method_template("player-execute", "HomeCommand", lstr("nothing"))
        client_socket.send(req)

        response = client_socket.recv(4096)
        test_response(self.logger, response, "(0,0,0)", [])

    def test_player_get_region(self, client_socket):
        self.logger.info("Testin get region")
        req = get_method_template("player-get-region", "", lstr())
        client_socket.send(req)

        response = client_socket.recv(4096)
        test_response(self.logger, response, "ARHUS", [])

    def test_player_get_position(self, client_socket):
        self.logger.info("Testing get position")
        req = get_method_template("player-get-position", "", lstr())
        client_socket.send(req)

        response = client_socket.recv(4096)
        test_response(self.logger, response, "(0,0,0)", [])

    def test_player_get_short_description(self, client_socket):
        self.logger.info("Testing get short room description")
        req = get_method_template("player-get-short-room-description", "", lstr())
        client_socket.send(req)

        response = client_socket.recv(4096)
        test_response(self.logger, response, "You are standing at the end of a road before a small brick building.", [])

    def test_player_get_long_description(self, client_socket):
        self.logger.info("Testing get long room description")
        req = get_method_template("player-get-long-room-description", "", lstr())
        client_socket.send(req)

        response = client_socket.recv(4096)
        test_response(self.logger, response, "You are standing at the end of a road before a small brick building.\nThere are exits in directions:\n  NORTH   EAST   WEST   UP \nYou see other players:\n  [0]", [])

    def test_player_get_exit_set(self, client_socket):
        self.logger.info("Testing get exit set")
        req = get_method_template("player-get-exit-set", "", lstr())
        client_socket.send(req)

        response = client_socket.recv(4096)
        test_response(self.logger, response, "notused", ["NORTH", "EAST", "WEST", "UP"])

    def test_player_move(self, client_socket):
        self.logger.info("Testing player move")
        req = get_method_template("player-move", "DOWN", lstr())
        client_socket.send(req)

        response = client_socket.recv(4096)
        test_response(self.logger, response, "false", [])
    
######################################
#                                    #
# EXECUTION                          #
#                                    #
######################################

def execute_friendly_crunch(handler):
    nice_peter = NicePeter(handler)
    
    reset_server()
    sock_handle(nice_peter.test_login)
    sock_handle(nice_peter.test_homecommand)
    sock_handle(nice_peter.test_player_get_region)
    sock_handle(nice_peter.test_player_get_position)
    sock_handle(nice_peter.test_player_get_short_description)
    sock_handle(nice_peter.test_player_get_long_description)
    sock_handle(nice_peter.test_player_get_exit_set)
    sock_handle(nice_peter.test_player_move)
    sock_handle(nice_peter.test_logout)

######################################
#                                    #
# CRASH THIS BABY                    #
#                                    #
######################################
class CrashBaby():
    def __init__(self, handler):
        self.logger = logging.getLogger("Crash Baby")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        
    def test_improper_line_ending(self, client_socket):
        self.logger.info("Trying to send improper line eding")
        req = get_method_template("player-execute", "HomeCommand", lstr("nothing"))[:-1]
        client_socket.send(req)

    def test_two_commands_improper_line_ending(self, client_socket):
        self.logger.info("Trying to send two commands with improper line eding")
        req = get_method_template("player-execute", "HomeCommand", lstr("nothing"))[:-1]
        client_socket.send(req+req)

    def test_two_commands_first_has_improper_line_ending(self, client_socket):
        self.logger.info("Trying to send two commands first with improper line eding")
        req = get_method_template("player-execute", "HomeCommand", lstr("nothing"))
        client_socket.send(req[:-1]+req)

        response = client_socket.recv(4096)
        test_error_response(self.logger, response, "GENERAL_SERVER_FAILURE", "JSON Parse error")

    def test_two_commands(self, client_socket):
        self.logger.info("Trying to send two commands first with improper line eding")
        req = get_method_template("player-execute", "HomeCommand", lstr("nothing"))
        client_socket.send(req+req)

        response = client_socket.recv(4096)
        test_response(self.logger, response, "(0,0,0)", [])

    def test_malicious_data(self, client_socket):
        self.logger.info("Sending null")
        try:
            client_socket.send(None)
        except:
            pass # Ignore the error, damage has been done!

    def test_empty_string(self, client_socket):
        self.logger.info("Sending empty string")
        client_socket.send(b"")

    def test_non_json(self, client_socket):
        self.logger.info("Sending non-json")
        client_socket.send(b"My tooth, my tooth, I think I lost my tooth\n")

        response = client_socket.recv(4096)
        test_error_response(self.logger, response, "GENERAL_SERVER_FAILURE", "JSON Parse error")

    def test_garbage_json(self, client_socket):
        self.logger.info("Sending wrong json")
        client_socket.send(b"{\"foo\": \"bar\"}\n")

        response = client_socket.recv(4096)
        test_error_response(self.logger, response, "GENERAL_SERVER_FAILURE", "JSON Parse error")

def execute_nasty_crunch(handler):
    nice_peter = NicePeter(handler)
    crashBaby = CrashBaby(handler)
    
    reset_server()
    sock_handle(nice_peter.test_login)

    sock_handle(crashBaby.test_improper_line_ending)
    sock_handle(crashBaby.test_two_commands_improper_line_ending)
    sock_handle(crashBaby.test_two_commands_first_has_improper_line_ending)
    sock_handle(crashBaby.test_two_commands)
    sock_handle(crashBaby.test_malicious_data)
    sock_handle(crashBaby.test_empty_string)
    sock_handle(crashBaby.test_non_json)
    sock_handle(crashBaby.test_garbage_json)

    sock_handle(nice_peter.test_logout)

if __name__ == "__main__":
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler("rfcruncher.log")
    handler.setFormatter(formatter)

    execute_friendly_crunch(handler)
    execute_nasty_crunch(handler)
