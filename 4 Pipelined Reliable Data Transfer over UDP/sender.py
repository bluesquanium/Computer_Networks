from socket import *
import threading
import time
import os

def fileSend(file_name, receiverIP, receiverPort) :
    #t_socket = socket(AF_INET, SOCK_DGRAM)
    
    #파일 이름 보내주기
    s_socket.sendto( f_name.encode(), (receiverIP, receiverPort) )
    #log_file 이름
    log_name = file_name + "_sending_log.txt"
    f_log = open(log_name, 'w')
    f_log.close()
    #time 측정 시작 및 check_time 선언 및 초기화
    start_time = time.time()
    check_time = start_time
    timeline = {}

    #파일 전송 시작
    #전송 예 : f_log.write("0.000 pkt: 0\t|\t received")
    seq = 0
    f_send = open(file_name, mode='rb')
    #getACK 시작, ack 초기화 및 check_ack 선언 및 초기화
    #ack = threading.Condition()
    global ack
    global dup_ack
    ack = -1
    dup_ack = 0
    check_ack = ack
    wanted_ack = ack-1 #timeout, duplicated ack 발생 시 원하는 ack 기다림. 시간도 체
    t = threading.Thread(target = getACK, args = (log_name, start_time))
    t.deamon = True
    t.start()

    while True :
        cur_time = time.time()
        # check_ack 값 업데이트 + time 체크를 위해
        if check_ack <= ack :
            check_ack = ack
            try :
                check_time = timeline[check_ack+1]
            except :
                #retransmit 하고 나서 ack을 받아 no key error가 발생할 경우
                check_time = time.time()
        # tiemout, duplicated ack 발생 시 원하는 ack 기다림.
        # 기다리는 도중 시간 오버되면 드랍 되서 timeout 된 것이므로 timeout 이벤트 발생
        if wanted_ack > check_ack and cur_time - check_time <= timeout :
            continue
            
        # 현재 seq보다 ack이 크면 seq를 ack+1로 옮겨줌
        if check_ack >= seq :
            f_send.seek(bufsize*(check_ack+1), os.SEEK_SET)
            seq = check_ack + 1

        # timeout일 때
        if cur_time - check_time > timeout :
            #커서 위치 옮김 + 패킷 전송
            f_send.seek(bufsize*(check_ack+1), os.SEEK_SET)
            chunk = f_send.read(bufsize)
            seq = check_ack+1 # seq위치도 옮겨줌
            if len(chunk) < 1 :
                if check_ack == seq-1 :
                    break
                else :
                    continue
            # 전송
            s = "file=%s;seq=%d" % (file_name, seq)
            s_socket.sendto( s.encode(), (receiverIP, receiverPort) )
            s_socket.sendto( chunk, (receiverIP, receiverPort) )
            # log 기록
            f_log = open(log_name, 'a')
            s = ( "%0.3f" % (cur_time - start_time) ) + " pkt: " + str(seq) + "\t|\t" + " timeout since " + ( "%0.3f" % (check_time - start_time) ) + "\n"
            #print(s)#확인용
            f_log.write(s)
            s = ( "%0.3f" % (cur_time - start_time) ) + " pkt: " + str(seq) + "\t|\t" + " retransmitted " + "\n"
            #print(s)#확인용
            f_log.write(s)
            f_log.close()
            # time 초기화
            timeline.clear()
            check_time = time.time()
            #timeline에 해당 패킷 보낸시간 저장
            timeline[seq] = cur_time
            seq += 1
            dup_ack = 0
            wnated_ack = check_ack+1
            continue
        
        # 3 duplicated ack
        if dup_ack >= 3 :
            #커서 위치 옮김 + 패킷 전송
            f_send.seek(bufsize*(check_ack+1), os.SEEK_SET)
            chunk = f_send.read(bufsize)
            seq = check_ack+1 # seq위치도 옮겨줌
            if len(chunk) < 1 :
                if check_ack == seq-1 :
                    break
                else :
                    continue
            # 전송
            s = "file=%s;seq=%d" % (file_name, seq)
            s_socket.sendto( s.encode(), (receiverIP, receiverPort) )
            s_socket.sendto( chunk, (receiverIP, receiverPort) )
            # log 기록
            f_log = open(log_name, 'a')
            s = ( "%0.3f" % (cur_time - start_time) ) + " pkt: " + str(seq-1) + "\t|\t" + " 3 duplicated ACKs " + "\n"
            #print(s)#확인용
            f_log.write(s)
            s = ( "%0.3f" % (cur_time - start_time) ) + " pkt: " + str(seq) + "\t|\t" + " sent " + "\n"
            #print(s)#확인용
            f_log.write(s)
            f_log.close()
            # time 초기화
            timeline.clear()
            check_time = time.time()
            #timeline에 해당 패킷 보낸시간 저장
            timeline[seq] = cur_time
            seq += 1
            dup_ack = 0
            wanted_ack = check_ack+1
            continue
        
        # seq가 window 넘어가면 멈춤
        if seq - check_ack > window :
            #print("Pause for window.")
            continue
        #파일 보내면서 log 파일 기록도 하기 (sent 완료, received 완료)
        #파일 재전송 케이스 구현 (3ack 구현, retransmit 구현, timeout 구현)
        chunk = f_send.read(bufsize)
        # 파일 마지막까지 다 보냈을 경우
        if len(chunk) < 1 :
            if check_ack == seq-1 :
                break
            else :
                continue
        # 전송
        s = "file=%s;seq=%d" % (file_name, seq)
        s_socket.sendto( s.encode(), (receiverIP, receiverPort) )
        s_socket.sendto( chunk, (receiverIP, receiverPort) )
        # 패킷 보낼 때마다 log file에 기록
        f_log = open(log_name, 'a')
        cur_time = time.time()
        s = ( "%0.3f" % (cur_time - start_time) ) + " pkt: " + str(seq) + "\t|\t" + " sent\n"
        #print(s)#확인용 
        f_log.write(s)
        f_log.close()
        #timeline에 해당 패킷 보낸시간 저장
        timeline[seq] = cur_time
        seq += 1
    # 전송 - 전송 끝났음을 알려줌
    s = "file=%s;seq=%d" % (file_name, -2)
    s_socket.sendto( s.encode(), (receiverIP, receiverPort) )
    s_socket.sendto( chunk, (receiverIP, receiverPort) )

    #t가 끝나길 기다린다.
    t.join()
    
    f_log = open(log_name, 'a')
    cur_time = time.time()
    f_log.write("File transfer is finished.\n")
    s = "Throughput: " + ("%0.2f" % (seq/(cur_time - start_time)) ) + " pkts / sec\n"
    #print(s)#확인용 
    f_log.write(s)

    f_log.close()
    f_send.close()

def getACK(log_name, start_time) :
    global ack
    global dup_ack
    t_socket = socket(AF_INET, SOCK_DGRAM)
    t_socket.setsockopt(SOL_SOCKET, SO_SNDBUF, 10000000)
    t_socket.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000000)
    t_socket.bind(('',10079))
    while True :
        #r_ack = -2
        message, address = t_socket.recvfrom( bufsize )
        #print(message.decode())
        for m in message.decode().split(sep=';') :
            if(m[0:3] == 'ack') :
                r_ack = int(m[4:])
                #print("r_ack updated! : %d" % r_ack)
        if r_ack == -2 :
            break
        f_log = open(log_name, 'a')
        cur_time = time.time()
        s = ( "%0.3f" % (cur_time - start_time) ) + " ACK: " + str(r_ack) + "\t|\t" + " received\n"
        if r_ack > ack :
            ack = r_ack
            dup_ack = 0
        elif r_ack == ack :
            dup_ack += 1
        #print(s)#확인용
        f_log.write(s)
        f_log.close()

    t_socket.close()

ack = -1
dup_ack = 0
s_socket = socket(AF_INET, SOCK_DGRAM)
s_socket.setsockopt(SOL_SOCKET, SO_SNDBUF, 10000000)
s_socket.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000000)

receiverIP = input("Receiver IP address : ")
window = int(input("Window size : "))
timeout = float(input("timeout (sec) : "))
#print(receiverIP, timeout, window)

receiverPort = 10080
#파일
bufsize = 1024

while True :
    f_name = input("file_name : ")

    if f_name == "quit" or f_name == "exit" :
        break
    else :
        #t = threading.Thread(target = fileSend, args=(f_name, receiverIP, receiverPort))
        #t.deamon = True
        #t.start()
        fileSend(f_name,receiverIP,receiverPort)
        

s_socket.close()
