from socket import *
import threading

user_id = ''
pw = ''

serverPort = 10080
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind( ('', serverPort) )
serverSocket.listen(20)
print("The TCP server is ready to receive.")

while True:
    connectionSocket, addr = serverSocket.accept()
    print("Got Request")
    for x in range(500) :
        t = threading.Thread()
        #t.daemon = True
        t.start()
        
    try:
        buffer = bytearray()
        chunk_size = 4096
        
        msg = connectionSocket.recv(1024).decode()
        m = ''
        #쿠키 체크
        user_id = pw = ''
        for s in msg.split() :
            if(s[0:7] == "User_ID") :
               #id, pw 저장
               value = s.split('&')
               user_id = value[0].split('=')[1]
               pw = value[1].split('=')[1]
               #쿠키를 코드에서 저장했을 경우
               #m = "HTTP/1.1 200 OK\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout=5, max=1000\r\nSet-Cookie: user_id="+user_id+"; max-age=30\r\nSet-Cookie: pw="+pw+"; max-age=30\r\n\r\n"
               break
            elif(s[0:7] == "user_id") :
                user_id = s[8:]
                break;
        filename = msg.split()[1]
        if(filename == '/') :
            filename = '/index.html'
        f = open(filename[1:], mode='rb')

        #print(user_id)
        #print(msg)
        #Send one HTTP header line into socket
        if((user_id == '') and filename != '/index.html' and filename != '/') :
            connectionSocket.send("HTTP/1.1 403 Forbidden\r\n\r\n".encode())
            connectionSocket.close()
            continue
        #여긴 쿠키를 코드에서 저장했을 경우
        #elif(m != '') : 
        #    connectionSocket.send(m.encode())
        else :
            connectionSocket.send("HTTP/1.1 200 OK\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout=5, max=1000\r\n\r\n".encode())
            
        while True :
            chunk = f.read(chunk_size)
            if len(chunk) < 1:
                break
            connectionSocket.send(chunk)
        connectionSocket.close()
        
    except IOError:
        connectionSocket.send("HTTP/1.1 404 Not Found\r\n\r\n".encode())
        connectionSocket.close()
    except IndexError:
        connectionSocket.send("HTTP/1.1 404 Not Found\r\n\r\n".encode())
        connectionSocket.close()
        
    #f = open(msg,mode='rb')
    #for line in f.readlines():
    #    newMsg = line
    #    connectionSocket.send( newMsg )
    #f.close()
    #connectionSocket.close()

serverSocket.close()
