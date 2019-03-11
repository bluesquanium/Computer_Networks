from socket import *
import threading
import time
import random

def packetReceive() : #NEM
    r_socket = socket(AF_INET, SOCK_DGRAM)
    r_socket.setsockopt(SOL_SOCKET, SO_SNDBUF, 10000000)
    r_socket.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000000)

    r_socket.bind(('', receiverPort))
    
    f_check = True # 처음 시작 체크해줌

    global stop
    global mailbox
    global start_time
    p_count = 0
    check_p = 0
    forward_count = 0
    check_forward = 0
    check_time = 2.000
    sec1 = time.time()
    ms100 = time.time()
    queue = [] # 큐 역할
    queue_util = []
    q_fill = 0

    #log_file 이름
    nem_name = "NEM.log"
    nem_log = open(nem_name, 'w')
    s = "time  |  incoming_rate  |  forwarding_rate  |  avg_queue_utilization\n"
    nem_log.write(s)
    nem_log.close()
    
    while stop == False :
        cur_time = time.time()
        if cur_time - ms100 >= 0.1 : # 100ms마다 실행
            if queue_size != 0 :
                queue_util.append((q_fill/queue_size))
            ms100 = time.time()
        if cur_time - start_time >= check_time:
            #print("len(queue) : %d, forward_count - check_forward : %d " % (len(queue), (forward_count - check_forward)/2)) #확인용
            if len(queue_util) != 0 :
                q = sum(queue_util)/len(queue_util)
            else :
                q = 0
            nem_log = open(nem_name, 'a')
            s = "%0.3f  |  " % (cur_time - start_time) + "%0.3f   \t|\t" % ((p_count - check_p)/2) + "%0.3f\t|\t" % ((forward_count)/2) + "%0.3f\n" % (q)
            nem_log.write(s)
            nem_log.close()

            queue_util.clear()
            check_time += 2
            check_p = p_count
            check_forward = forward_count = 0
        
        #패킷 받는다.
        message, senderAddress = r_socket.recvfrom( packetsize )
        p_count += 1
        #처음 시작 시 start_time 초기화
        if f_check == True :
            f_check = False
            start_time = time.time()

        #받은 seq번호 저장
        for m in message.decode().split(sep=';') :
            if(m[0:3] == 'seq') :
                r_seq = int(m[4:])
            if(m[0:4] == 'port') :
                r_port = int(m[5:])
        if forward_count - check_forward >= blr : # blr에 따른 제어
            if(q_fill < queue_size) :
                if q_fill == 0 :
                    queue.append((senderAddress, r_seq, r_port))
                    q_fill += 1
                elif random.random() < 1/(q_fill*q_fill) :
                    queue.append((senderAddress, r_seq, r_port))
                    q_fill += 1
        else : # RM으로 보내지는 패킷들
            if q_fill > 0 :
                mailbox = mailbox + queue[:forward_count - check_forward]
                queue = queue[forward_count - check_forward:]
                q_fill = len(queue)
                forward_count += len(queue[:forward_count - check_forward])
                if(forward_count - check_forward < blr) :
                    mailbox.append((senderAddress, r_seq, r_port))
                    forward_count += 1
            else :
                mailbox.append((senderAddress, r_seq, r_port))
                forward_count += 1


def fileReceive() : #RM
    r_socket = socket(AF_INET, SOCK_DGRAM)
    r_socket.setsockopt(SOL_SOCKET, SO_SNDBUF, 10000000)
    r_socket.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000000)

    r_socket.bind(('', 0))
    
    global stop
    global mailbox
    global start_time
    check_time = 2.000
    seq_array = {} # 여기에 seq들 저장
    p_rec_array = {} # 2초당 패킷 받은 수 저장
    
    #log_file 이름
    rm_name = "RM.log"
    rm_log = open(rm_name, 'w')
    rm_log.close()
        
    while stop == False :
        cur_time = time.time()
        if mailbox != [] :
            p = mailbox.pop(0) #p[0][0] : senderIP, p[0][1] : senderPort, p[1] : seq, p[2] : senderAckPort
            temp = (p[0][0], int(p[0][1]))
            if temp in seq_array :
                p_rec_array[temp] += 1
                if seq_array[temp] == p[1]-1 : # 다음 패킷 받았으면 업데이트, 못받았으면 업데이트X
                    seq_array[temp] = p[1]
            else : # 해당 ip, port seq에 해당하는 seq 초기화
                p_rec_array[temp] = 1
                if p[1] == 0 :
                    seq_array[temp] = 0
                else :
                    seq_array[temp] = -1
            #s = "ack=%d" % (seq_array[(p[0][0], int(p[0][1]))])
            s = "ack=%d" % (p[1]) # s 수정
            r_socket.sendto( s.encode(), (p[0][0], p[2] )) # p[2]는 sender의 ack_port 번호
            
        if cur_time - start_time >= check_time:
            #print(s)
            rm_log = open(rm_name, 'a')
            _sum_pow = _sum = 0
            len_p_rec_array = 0
            for key in p_rec_array :
                if p_rec_array[key] != 0 :
                    _sum_pow += (p_rec_array[key]/2) * (p_rec_array[key]/2)
                    _sum += p_rec_array[key]/2
                    len_p_rec_array += 1
            if _sum_pow == 0 or len_p_rec_array == 0 :
                jf = 0
            else :
                jf = (_sum * _sum)/(len_p_rec_array * _sum_pow)
            s = "%0.3f  |  " % (cur_time - start_time) + "%0.3f\n" % jf
            rm_log.write(s)
            for key in p_rec_array :
                s = "\t%s:%d\t|\t" % (key[0], key[1]) + "%0.3f\n" % (p_rec_array[key]/2)
                rm_log.write(s)
                p_rec_array[key] = 0
                
            rm_log.close()

            check_time += 2
        

    rm_log.close()

receiverPort = 10080
packetsize = 1400
command = input("configure>>")
command = command.split(" ")
blr = int(command[0]) * 2
queue_size = int(command[1])
mailbox = [] # 보내진 패킷들 저장
stop = False

print("receiver program starts...")

#시간 측정 시작
start_time = time.time() + 100000 #NEM에서 받기 시작한 이후부터 시간 측정시작

#NEM
t1 = threading.Thread(target = packetReceive)
t1.deamon = True
t1.start()
#RM
t2 = threading.Thread(target = fileReceive)
t2.deamon = True
t2.start()

while True :
    command = input("프로그램을 끝내기 원한다면 stop을 입력해주세요.\nconfigure>>")
    if command == "stop" :
        stop = True
        t2.join()
        break
