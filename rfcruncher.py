import pika
import socket
import urllib
import json
import string
import traceback

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

def test_response(response, reply, tail):
    try:
        print(response)
        res = json.loads(response)
        reply_tail = []
        if 'reply-tail' in res:
            reply_tail = res['reply-tail']
            
        error_code = res['error-code']
        if error_code != "OK":
            print("Error in the response, the returned data was: ", response)
            raise TestError('Test failed')

        error_message = res['error-message']
        json_reply = res['reply']
        if not reply in json_reply:
            print("Unexpected response in the reply field: ", json_reply)
            print("Complete json is: ", response)
            raise TestError('Test failed')

        for x in tail:
            if x not in reply_tail:
                print("Unexpected reply tail recieved, could not find the item: ", x)
                print("The tail received was: ", reply_tail)
                raise TestError('Test failed')
    except:
        raise TestError("Test failed")
            
    print(" *** HURRAY *** ")

def test_error_response(response, code, message):
    try:
        res = json.loads(response)
            
        error_code = res['error-code']
        if not code in error_code:
            print("Error in the error code, the returned data was: ", response)
            raise TestError('Test failed')

        error_message = res['error-message']
        if not message.upper() in error_message.upper():
            print("Unexpected error message: ", error_message)
            print("Expected to contain: ", message)
            print("Complete json is: ", response)
            raise TestError('Test failed')

    except:
        print(traceback.format_exc())
        raise TestError("Test failed")
            
    print(" *** HURRAY *** ")

    
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
    
def reset_server():
    print("Resetting server")

    def conn(client_socket):
        req = method_template.format("cave-login", player_login, lstr(player_pass), player_id, player_session)

        client_socket.send(req)
        response = client_socket.recv(4096)
        res = json.loads(response)
        set_user_details(res['reply-tail'])
    sock_handle(conn)
        
    def dis_conn(client_socket):
        req = method_template.format("cave-logout", "", lstr(), player_id, player_session)

        client_socket.send(req)
        response = client_socket.recv(4096)
        reset_user_details()
    sock_handle(dis_conn)

######################################
#                                    #
# TESTS                              #
#                                    #
######################################
    
def test_login(client_socket):
    print("Logging in")
    req = method_template.format("cave-login", player_login, lstr(player_pass), player_id, player_session)
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "LOGIN_SUCCESS", ["55e45169e4b067dd3c8fa56e", "rohdef"])
    res = json.loads(response)
    set_user_details(res['reply-tail'])
    

def test_logout(client_socket):
    print("Logging out")
    req = method_template.format("cave-logout", "", lstr(), player_id, player_session)
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "SUCCESS", [])

def test_homecommand(client_socket):
    print("Testing home command")
    req = method_template.format("player-execute", "HomeCommand", lstr("nothing"), player_id, player_session)
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "(0,0,0)", [])

def test_player_get_region(client_socket):
    print("Testin get region")
    req = method_template.format("player-get-region", "", lstr(), player_id, player_session)
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "ARHUS", [])

def test_player_get_position(client_socket):
    print("Testing get position")
    req = method_template.format("player-get-position", "", lstr(), player_id, player_session)
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "(0,0,0)", [])

def test_player_get_short_description(client_socket):
    print("Testing get short room description")
    req = method_template.format("player-get-short-room-description", "", lstr(), player_id, player_session)
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "You are standing at the end of a road before a small brick building.", [])

def test_player_get_long_description(client_socket):
    print("Testing get long room description")
    req = method_template.format("player-get-long-room-description", "", lstr(), player_id, player_session)
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "You are standing at the end of a road before a small brick building.\nThere are exits in directions:\n  NORTH   EAST   WEST   UP \nYou see other players:\n  [0]", [])

def test_player_get_exit_set(client_socket):
    print("Testing get exit set")
    req = method_template.format("player-get-exit-set", "", lstr(), player_id, player_session)
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "notused", ["NORTH", "EAST", "WEST", "UP"])

def test_player_move(client_socket):
    print("Testing player move")
    req = method_template.format("player-move", "DOWN", lstr(), player_id, player_session)
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "false", [])
    
######################################
#                                    #
# EXECUTION                          #
#                                    #
######################################
    
reset_server()
sock_handle(test_login)
sock_handle(test_homecommand)
sock_handle(test_player_get_region)
sock_handle(test_player_get_position)
sock_handle(test_player_get_short_description)
sock_handle(test_player_get_long_description)
sock_handle(test_player_get_exit_set)
sock_handle(test_player_move)
sock_handle(test_logout)

######################################
#                                    #
# CRASH THIS BABY                    #
#                                    #
######################################
def test_improper_line_ending(client_socket):
    print("Trying to send improper line eding")
    req = method_template.format("player-execute", "HomeCommand", lstr("nothing"), player_id, player_session)[:-1]
    client_socket.send(req)

def test_two_commands_improper_line_ending(client_socket):
    print("Trying to send two commands with improper line eding")
    req = method_template.format("player-execute", "HomeCommand", lstr("nothing"), player_id, player_session)[:-1]
    client_socket.send(req+req)

    #response = client_socket.recv(4096)
 

def test_two_commands_first_has_improper_line_ending(client_socket):
    print("Trying to send two commands first with improper line eding")
    req = method_template.format("player-execute", "HomeCommand", lstr("nothing"), player_id, player_session)
    client_socket.send(req[:-1]+req)

    response = client_socket.recv(4096)
    test_error_response(response, "GENERAL_SERVER_FAILURE", "JSON Parse error")

def test_two_commands(client_socket):
    print("Trying to send two commands first with improper line eding")
    req = method_template.format("player-execute", "HomeCommand", lstr("nothing"), player_id, player_session)
    client_socket.send(req+req)

    response = client_socket.recv(4096)
    test_response(response, "(0,0,0)", [])
    #    test_error_response(response, "GENERAL_SERVER_FAILURE", "JSON Parse error")

def test_malicious_data(client_socket):
    print("Sending null")
    try:
        client_socket.send(None)
    except:
        pass # Ignore the error, damage has been done!

def test_empty_string(client_socket):
    print("Sending empty string")
    client_socket.send("")

def test_non_json(client_socket):
    print("Sending non-json")
    client_socket.send("My tooth, my tooth, I think I lost my tooth\n")

    response = client_socket.recv(4096)
    test_error_response(response, "GENERAL_SERVER_FAILURE", "JSON Parse error")

def test_garbage_json(client_socket):
    print("Sending wrong json")
    client_socket.send("{\"foo\": \"bar\"}\n")

    response = client_socket.recv(4096)
    test_error_response(response, "GENERAL_SERVER_FAILURE", "JSON Parse error")
    
reset_server()
sock_handle(test_login)
sock_handle(test_improper_line_ending)
sock_handle(test_two_commands_improper_line_ending)
sock_handle(test_two_commands_first_has_improper_line_ending)
sock_handle(test_two_commands)
sock_handle(test_malicious_data)
sock_handle(test_empty_string)
sock_handle(test_non_json)
sock_handle(test_garbage_json)
sock_handle(test_logout)
