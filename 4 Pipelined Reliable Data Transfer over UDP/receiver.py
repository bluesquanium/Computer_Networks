from socket import *
import threading
import time
import random

def fileReceive(file_name, senderIP, senderPort) :
    tempbuf = []
    log_name = file_name + "_receiving_log.txt"
    f_log = open(log_name, 'w')
    #time 측정 시작
    start_time = time.time()

    #파일 받기 시작
    print("Start Receiving")
    #받는 예 : f_log.write("0.000 pkt: 0\t|\t received")
    seq = 0
    f_rec = open(file_name, mode='wb')
    while True :
        #파일 보내면서 log 파일 기록도 하기 (sent 구현, received 구현)
        m_info, senderAddress = r_socket.recvfrom( bufsize )
        message, senderAddress = r_socket.recvfrom( bufsize )
        #print(m_info.decode())
        for m in m_info.decode().split(sep=';') :
            if(m[0:3] == 'seq') :
                r_seq = int(m[4:])
        # 빠져나오는 조건
        if r_seq == -2 :
            s = "file=%s;ack=%d" % (file_name, -2)
            r_socket.sendto( s.encode(), (senderIP, 10079) )
            break
        # 패킷 받을 때마다 log file에 기록
        cur_time = time.time()
        s = ( "%0.3f" % (cur_time - start_time) ) + " pkt: " + str(r_seq) + "\t|\t" + " received\n"
        #print(s) #확인용
        f_log.write(s)
        #prob 값에 따른 패킷 드랍
        if random.random() < prob :
            s = ( "%0.3f" % (cur_time - start_time) ) + " pkt: " + str(r_seq) + "\t|\t" + " dropped\n"
            #print(s) #확인용
            f_log.write(s)
            continue
        # seq보다 큰 파일 받았을 경우 temporary buffer에 저장
        if seq < r_seq :
            #print("Save %d, len=%d" % (r_seq, len(tempbuf)))
            tempbuf = addTempbuf(tempbuf, (r_seq, message))
        #ACK 보내주기
        if seq == r_seq :
            f_rec.write(message)
            seq += 1
            # f_rec.write한 패킷들은 버리기
            while tempbuf != [] and tempbuf[0][0] < seq :
                #print("del %d, len=%d" % (seq, len(tempbuf)))
                del tempbuf[0]
            # tempbuf에 저장된 패킷 저장
            while tempbuf != [] and tempbuf[0][0] == seq :
                #print("write %d, len=%d" % (seq, len(tempbuf)))
                f_rec.write(tempbuf[0][1])
                del tempbuf[0]
                seq += 1
            s = "file=%s;ack=%d" % (file_name, seq-1)
            s2 = ( "%0.3f" % (cur_time - start_time) ) + " ACK: " + str(seq-1) + "\t|\t" + " sent\n"
        else :
            s = "file=%s;ack=%d" % (file_name, seq-1)
            s2 = ( "%0.3f" % (cur_time - start_time) ) + " ACK: " + str(seq-1) + "\t|\t" + " sent\n"
        r_socket.sendto( s.encode(), (senderIP, 10079) )
        #print(s2)
        f_log.write(s2)
    cur_time = time.time()
    f_log.write("File transfer is finished.\n")
    s = "Throughput: " + ( "%0.2f" % (seq/(cur_time - start_time)) ) + " pkts / sec\n"
    print(s) #확인용
    f_log.write(s)
    f_log.close()
    f_rec.close()

#buf에 작은 수부터 순서대로 저장하기 위한 함수
def addTempbuf(buf, tup) :
    if len(buf)==0 :
        buf.append(tup)
    for i in range(0, len(buf)) :
        if buf[i][0] == tup[0] :
            return buf
        elif buf[i][0] > tup[0] :
            buf.insert(i, tup)
            break
        elif buf[i][0] < tup[0] and i == len(buf)-1 :
            buf.insert(i+1, tup)
            break
    return buf

r_socket = socket(AF_INET, SOCK_DGRAM)
r_socket.setsockopt(SOL_SOCKET, SO_SNDBUF, 10000000)

bufsize = 1024
prob = float(input("packet loss probability: "))
bufsize_updated = r_socket.getsockopt(SOL_SOCKET, SO_RCVBUF)
print("socket recv buffer size: ", bufsize)
r_socket.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000000)
bufsize_updated = r_socket.getsockopt(SOL_SOCKET, SO_RCVBUF)
print("socket recv buffer size updated: ", bufsize_updated)

receiverPort = 10080
r_socket.bind(('', receiverPort))
print("receiver program starts...")

while True :
    # 파일 이름 받는다.
    message, senderAddress = r_socket.recvfrom( bufsize )
    # sender의 메인 포트번호 저장
    
    file_name = message.decode()
    print(file_name)
    # sender에게 bufsize 보내준다.
    #r_socket.sendto( bufsize.encode(), senderAddress )

    ### 쓰레딩은 나중에
    #t = threading.Thread(target = fileReceive, args = (file_name, senderAddress, receiverPort))
    #t.deamon = True
    #t.start()
    fileReceive(file_name, senderAddress[0], 10079)
    
    #r_socket.sendto( newMsg.encode(), clientAddress)
