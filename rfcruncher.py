import pika
import json
import string
import traceback
import logging
from testutils import TestRunner, test_error_response
from testutils import lstr
from testutils import test_response

######################################
#                                    #
#  CONFIGURATION                     #
#                                    #
######################################
host = "cave.smatso.dk"
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
# CRASH THIS BABY                    #
#                                    #
######################################
class CrashBaby():
    def __init__(self, handler):
        self.logger = logging.getLogger("Crash Baby")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self.logger.info("Crash Baby active")
        
    def test_improper_line_ending(self, client_socket):
        self.logger.info("Trying to send improper line eding")
        req = get_method_template("player-execute", "HomeCommand", lstr("nothing"))
        client_socket.send(req[:-1])

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


######################################
#                                    #
# EXECUTION                          #
#                                    #
######################################
class TestSuite:
    def __init__(self, handler, useRabbit=False):
        self.handler = handler
        self.runner = TestRunner(handler, host, port, useRabbit)
        self.logger = logging.getLogger("Test suite")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def get_test_tuple(self):
        return self.runner.get_test_tuple()
        
    def reset_server(self):
        def conn(client_socket):
            req = get_method_template("cave-login", player_login, lstr(player_pass))

            client_socket.send(req)
            response = client_socket.recv(4096)
            res = json.loads(response.decode("utf-8"))
            set_user_details(res['reply-tail'])
        self.runner.runTest(conn)
        
        def dis_conn(client_socket):
            req = get_method_template("cave-logout", "", lstr())

            client_socket.send(req)
            response = client_socket.recv(4096)
            reset_user_details()
        self.runner.runTest(dis_conn)
    
    def execute_friendly_crunch(self):
        nice_peter = NicePeter(self.handler)
    
        self.reset_server()
        self.runner.runTest(nice_peter.test_login)
        self.runner.runTest(nice_peter.test_homecommand)
        self.runner.runTest(nice_peter.test_player_get_region)
        self.runner.runTest(nice_peter.test_player_get_position)
        self.runner.runTest(nice_peter.test_player_get_short_description)
        self.runner.runTest(nice_peter.test_player_get_long_description)
        self.runner.runTest(nice_peter.test_player_get_exit_set)
        self.runner.runTest(nice_peter.test_player_move)
        self.runner.runTest(nice_peter.test_logout)

    def execute_nasty_crunch(self):
        nice_peter = NicePeter(self.handler)
        crashBaby = CrashBaby(self.handler)
    
        self.reset_server()
        self.runner.runTest(nice_peter.test_login)

        self.runner.runTest(crashBaby.test_improper_line_ending)
        self.runner.runTest(crashBaby.test_two_commands_improper_line_ending)
        self.runner.runTest(crashBaby.test_two_commands_first_has_improper_line_ending)
        self.runner.runTest(crashBaby.test_two_commands)
        self.runner.runTest(crashBaby.test_malicious_data)
        self.runner.runTest(crashBaby.test_empty_string)
        self.runner.runTest(crashBaby.test_non_json)
        self.runner.runTest(crashBaby.test_garbage_json)

        self.runner.runTest(nice_peter.test_logout)

if __name__ == "__main__":    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    #handler = logging.FileHandler("rfcruncher.log")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    testSuite = TestSuite(handler, False)
    testSuite.execute_friendly_crunch()
    testSuite.execute_nasty_crunch()

    logger = logging.getLogger("rfcruncher")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info(" *** We ran {0} tests, {1} of them was successes, {2} was failures and {3} made errors. *** ".format(*testSuite.get_test_tuple()))
