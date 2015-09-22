import pika
import socket
import urllib
import json

host = "cave.smatso.dk"
port = 57005

def test_response(response, reply, tail):
    res = json.loads(response)
    reply_tail = []
    if 'reply-tail' in res:
        reply_tail = res['reply-tail']
    error_code = res['error-code']
    error_message = res['error-message']
    json_reply = res['reply']

    if error_code != "OK":
        print("Error in the response, the returned data was: ", response)
        return

    if json_reply != reply:
        print("Unexpected response in the reply field: ", json_reply)
        print("Complete json is: ", response)
        return

    for x in tail:
        if x not in reply_tail:
            print("Unexpected reply tail recieved, could not find the item: ", x)
            print("The tail received was: ", reply_tail)
            return

    print(" *** HURRAY *** ")

def sock_handle(fun):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    fun(client_socket)
    client_socket.close()
    
def reset_server():
    print("Resetting server")

    def conn(client_socket):
        req = '{"method":"cave-login","parameter":"mikkel_aarskort","parameter-tail":["123"],"player-id":"ignore-player-id","version":"2","player-session-id":"ignore-session-id"}\n'
        client_socket.send(req)
        response = client_socket.recv(4096)
    sock_handle(conn)
        
    def dis_conn(client_socket):
        req = '{"method":"cave-logout","parameter":"","player-id":"user-001","version":"2","player-session-id":"ignore-session-id"}\n'
        client_socket.send(req)
        response = client_socket.recv(4096)
    sock_handle(dis_conn)

def test_login(client_socket):
    print("Logging in")
    req = '{"method":"cave-login","parameter":"mikkel_aarskort","parameter-tail":["123"],"player-id":"ignore-player-id","version":"2","player-session-id":"ignore-session-id"}\n'
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "LOGIN_SUCCESS", ["user-001", "Mikkel"])

def test_logout(client_socket):
    print("Logging out")
    req = '{"method":"cave-logout","parameter":"","player-id":"user-001","version":"2","player-session-id":"ignore-session-id"}\n'
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "SUCCESS", [])

def test_homecommand(client_socket):
    print("Testing home command")
    req = '{"method":"player-execute","parameter":"HomeCommand","parameter-tail":["nothing"],"player-id":"user-reserved","version":"2","player-session-id":"04dd1788-3b00-4da8-9315-f0401f832c9c"}\n'
    client_socket.send(req)

    response = client_socket.recv(4096)
    test_response(response, "SUCCESS", [])
    
reset_server()
sock_handle(test_login)
sock_handle(test_homecommand)
sock_handle(test_logout)
