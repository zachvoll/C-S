#Author: Zachary Vollen
import sys, socket, threading, select, hashlib

'''
creates a packet to be sent over the network layer.
seqno = sequence number,
last is a bool that indicates this packet is an ack or the last packet or a regular packet
data is the data being sent, ackbool is if the packet is supposed to be an ack or not
'''

def createPacket(seqno, last, data, ackbool):

	#seqno
	packet = chr(seqno)

	#size
	size = len(data).zfill(3)
	packet += size

	#last
	if ackbool:
		packet += '2'

	else:
		if(last):
			packet += '1'
		else:
			packet += '0'

	#add and pad data
	data = data.ljust(467,'\0')
	packet += data

	#compute checksum
	hash_object = hashlib.sha1(b(packet))
	checksum = hash_object.hexdigest()

	packet = checksum + packet

	return packet

#checkPacket returns the case, data, and seqno
def checkPacket(packet, seqval, ackbool):
	#string components of the packet
	checksum = packet[:40]
	seqno = packet[40]
	size = packet[41:44]
	last = packet[44]
	data = packet[45:]

	#everything in packet excluding the checksum
	excs = packet[40:]

	seq = ord(seqno)

	#compute checksum
	hash_object = hashlib.sha1(b(excs))
	checksum2 = hash_object.hexdigest()

	if(checksum == checksum2):

		if(last == 2 and seq != seqval):
			return ("dupack", "", seq)

		elif(seq != seqval):
			return ("dup", "", seq)

		elif(last == 2):
			return ("ack", "", seq)

		elif(last == 1):
			thesize = int(size)
			info = data[thesize:]
			return ("datalast", info, seq)

		else:
			thesize = int(size)
			return("data", data, seq)

	else:
		return ("corrupt", "", 0)

#client component of the program
def client():
	global host,port,inputfile

	#client socket setup
	cSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	cSock.connect((host, port))

	#initial timeout
	timeout = 2.0

	#read file
	with open(inputfile, 'r') as myfile:
		content = myfile.read()
		myfile.close()

	succ = 0
	maxwait = sys.maxint

	seqno = 0
	sendpacket = createPacket(seqno, False, inputfile, False)
	#deliver file name
	pktdel = False
	while not pktdel:
		#client sends packet
		cSock.sendall(sendpacket.encode())

		ready = select.select([cSock], [], [], timeout)
		if ready[0]:
			#get packet
			recvpacket = cSock.recv(512).decode()

			#check what the packet is
			case,data,seq = checkPacket(recvpacket, seqno, True)
			if(case == "ack"):
				seq = int(data)
				if(seq == seqno):
					pktdel = True

					if(timeout < maxwait):
						maxwait = timeout

		else:
			#add half a second to timeout, retransmit
			if(timeout < maxwait):
				timeout += 0.5
			print("Timeout! Retransmitting...")

	#update sequence number
	seqno = 1
	succ += 1

	lastpacket = False
	while not lastpacket:

		#prepare packet
		conlen = len(content)
		if(conlen < 467):
			lastpacket = True
			data = content
		else:
			data = content[:467]
			content = content[467:]

		sendpacket = createPacket(seqno, lastpacket, data)

		#start packet transmission
		pktdel = False
		while not pktdel:
			#client sends packet
			cSock.sendall(sendpacket.encode())

			ready = select.select([cSock], [], [], timeout)
			if ready[0]:
				#get packet
				recvpacket = cSock.recv(512).decode()

				#check what the packet is
				case,data,seq = checkPacket(recvpacket, seqno, True)

				if(case == "ack"):
					seq = int(data)
					if(seq == seqno):
						pktdel = True

						if(timeout < maxwait):
							maxwait = timeout

						succ += 1
						if(succ > 3):
							succ = 0
							timeout -= 0.5

			else:
				#increase wait time, retransmit
				if(timeout < maxwait):
					timeout += 0.5
				print("Timeout! Retransmitting...")

		#update sequence number
		seqno += 1

	#we're done sending the file, so close the socket
	cSock.shutdown()
	cSock.close()
	return None

#server component of the program
def server():
	global host,port

	#server socket setup
	cx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	cx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	cx.bind((host, port))
	cx.listen(20)

	sSock, addr = cx.accept()

	timeout = 2.0
	seqno = 0

	#get file path
	pktrecv = False
	while not pktrecv:
		recvpacket = sSock.recv(512).decode()
		case,data,seq = checkPacket(recvpacket, seqno, False)
		if(case == "data"):
			pktrecv = True

	#create ack
	sendpacket = createPacket(seqno, False, "", True)

	#send filename ack
	sSock.sendall(sendpacket.encode())
	seqno = 1

	#open file
	myfile = open(data, 'w+')

	#get packets and write them to file
	lastpkt = False
	while not lastpkt:
		recvpacket = sSock.recv(512).decode()
		case,data,seq = checkPacket(recvpacket, seqno, False)

		if(case == "dup"):
			sendpacket = createPacket(seq, False, "", True)
			sSock.sendall(sendpacket.encode())

		elif(case == "data"):
			myfile.write(data)

			sendpacket = createPacket(seq, False, "", True)
			sSock.sendall(sendpacket.encode())
			seqno += 1

		elif(case == "datalast"):
			myfile.write(data)

			sendpacket = createPacket(seq, False, "", True)
			sSock.sendall(sendpacket.encode())
			seqno += 1
			lastpkt = True

	myfile.close()
	sSock.shutdown()
	sSock.close()

def main():
	global host,port,inputfile

	numarg = len(sys.argv)
	if (numarg == 4):
		print("a")
		#get input arguments
		host,port,inputfile = str(sys.argv[1]),int(sys.argv[2]),str(sys.argv[3])
		client()

	elif(numarg == 3):
		print("b")
		host,port = str(sys.argv[1]),int(sys.argv[2])
		server()
	else:
		print("incorrect arguments, usage: <host> <port> <inputfile>")

main()
