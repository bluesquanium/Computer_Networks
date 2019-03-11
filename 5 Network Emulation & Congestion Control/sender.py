from socket import *
import threading
import time
import os

def fileSend(file_name, receiverIP, receiverPort) :
    global port_ack
    global stop
    global ack
    global dup_ack
    global timeout
    global window
    ack = -1
    dup_ack = 0
    check_ack = ack
    wanted_ack = ack-1
    seq = 0
    check_seq = -1 # 얘 check_ack 임. 하지만 check_ack을 예전에 구현해놔서!
    p_count = 0
    check_p = 0
    rtt = timeout
    timeline = {} # 패킷 보낸 시간 저장 -> timeout 및 RTT 계산 위해
    #시간 측정 시작
    start_time = time.time()
    check_time = 2
    timer = start_time
    wait_time  = start_time # timeout, dupAck 발생 시 기다리는 시간

    #log_file 이름
    log_name = str(port_num) + "_log.txt"
    f_log = open(log_name, 'w')
    s = "time\t|\targ_RTT\t|\tSR\t\t|\tG\n"
    f_log.write(s)
    f_log.close()
    
    while stop != True :
        cur_time = time.time()
        #print("cur_time - timer : %0.3f, timeout : %0.3f, ack : %d, check_ack : %d" % (cur_time-timer, timeout, ack, check_ack))
        if cur_time - start_time >= check_time:
            #print("window : %d" % window)
            #print("timeout : %0.3f, cur-timer : %0.3f" % (timeout, cur_time-timer))
            s = "%0.3f\t|\t" % (cur_time - start_time) + "%0.3f\t|\t" % (rtt) + "%0.3f      \t|\t" % ((p_count - check_p)/2) + "%0.3f\n" % ((check_ack - check_seq)/2)
            f_log = open(log_name, 'a')
            f_log.write(s)
            f_log.close()
            #print(s)

            #rtt_table.clear()
            check_time += 2
            check_p = p_count
            check_seq = check_ack
        
        # check_ack 값 업데이트 + time 체크를 위해
        if check_ack <= ack :
            temp = check_ack            
            check_ack = ack
            try :
                timer = timeline[check_ack+1]
                if temp != check_ack :
                    timeout = 0.5 + 1.5 * (cur_time - timeline[check_ack]) #timeout 업데이트 (RTT*1.5)
                    rtt = (rtt + (cur_time - timeline[check_ack]))/2
            except :
                #retransmit 하고 나서 ack을 받아 no key error가 발생할 경우
                timer = timer

        # tiemout, duplicated ack 발생 시 원하는 ack 기다림.
        # 기다리는 도중 시간 오버되면 드랍 되서 timeout 된 것이므로 timeout 이벤트 발생
        if wanted_ack > check_ack and cur_time - timer <= timeout :
            continue

        # 현재 seq보다 ack이 크면 seq를 ack+1로 옮겨줌
        if check_ack >= seq :
            seq = check_ack + 1

        #wait_time 넘지 않았으면 seq 전송하지 않고 기다리고 있기
        #if cur_time < wait_time :
        #    continue

        # timeout일 때
        if cur_time - timer > timeout :
            #print("timeout")
            #패킷 전송
            seq = check_ack+1 # seq위치도 옮겨줌
            # 전송
            s = "seq=%d;port=%d" % (seq, port_ack)
            s_socket.sendto( s.encode(), (receiverIP, receiverPort) )
            #print(s) #확인용
            
            timeline.clear() # timeline 초기화
            timer = time.time() # time 초기화
            wait_time = timer + rtt # timeout이나 dupAck 발생 시 rtt동안 ack 와도 기다림
            timeline[seq] = cur_time #timeline에 해당 패킷 보낸시간 저장
            seq += 1
            p_count += 1
            dup_ack = 0
            wnated_ack = check_ack+1
            window = window/2 + 5 # window 사이즈 1/2
            continue
            
        # 3 duplicated ack
        if dup_ack >= 3 :
            #print("dup")
            #패킷 전송
            seq = check_ack+1 # seq위치 옮겨줌
            # 전송
            s = "seq=%d;port=%d" % (seq, port_ack)
            #print(s) #확인용
            s_socket.sendto( s.encode(), (receiverIP, receiverPort) )
            # time 초기화
            timeline.clear()
            timer = time.time()
            wait_time = timer + rtt # timeout이나 dupAck 발생 시 rtt동안 ack 와도 기다림
            timeline[seq] = cur_time #timeline에 해당 패킷 보낸시간 저장
            seq += 1
            p_count += 1
            dup_ack = 0
            wanted_ack = check_ack+1
            window = window/2 + 5 # window 사이즈 1/2
            continue
        
        # seq가 window 넘어가면 멈춤
        if seq - check_ack > window :
            continue

        s = "seq=%d;port=%d" % (seq, port_ack)
        #print(s) #확인용
        s_socket.sendto( s.encode(), (receiverIP, receiverPort) )
        timeline[seq] = cur_time #timeline에 해당 패킷 보낸시간 저장
        seq += 1
        p_count += 1
    #receiver에게 전송 끝났다고 알려주기
    seq = -2
    s = "seq=%d;port=%d" % (seq, port_ack)
    s_socket.sendto( s.encode(), (receiverIP, receiverPort) )

    f_log.close()

def getACK() :
    global port_ack
    global ack
    global dup_ack
    global stop
    global window
    t_socket = socket(AF_INET, SOCK_DGRAM)
    t_socket.setsockopt(SOL_SOCKET, SO_SNDBUF, 10000000)
    t_socket.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000000)
    t_socket.bind(('',0)) # 이거 10079가 아닌 랜덤으로 나중에 바꾸기
    port_ack = t_socket.getsockname()[1]

    while stop != True :
        message, address = t_socket.recvfrom( packetsize )
        #print(message.decode())
        for m in message.decode().split(sep=';') :
            if(m[0:3] == 'ack') :
                #print(m) #확인
                r_ack = int(m[4:])
        if r_ack == -2 :
            break
        
        if r_ack > ack :
            ack = r_ack
            dup_ack = 0
            window += 1
        elif r_ack == ack :
            dup_ack += 1

    t_socket.close()

ack = 0
dup_ack = 0
stop = False
timeout = 1.00

receiverPort = 10080
packetsize = 1400
s_socket = socket(AF_INET, SOCK_DGRAM)
s_socket.setsockopt(SOL_SOCKET, SO_SNDBUF, 10000000)
s_socket.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000000)
s_socket.bind(('',0))

receiverIP = input("Receiver IP address : ")

#getAck부터 먼저 시작
port_ack = 0
t2 = threading.Thread(target = getACK)
t2.deamon = True
t2.start()

while True :
    command = input("command>>")
    command = command.split(" ")
    if(command[0] == "start") :
        window = int(command[1])
        port_num = s_socket.getsockname()[1]
        t = threading.Thread(target = fileSend, args=("", receiverIP, receiverPort))
        t.deamon = True
        t.start()
    elif command[0] == "stop" :
        stop = True

        #쓰레드 끝나기를 기다린다
        t.join()
        break
    else :
        print("Command error. Please check your command. ('stop' : exit)")

s_socket.close()
