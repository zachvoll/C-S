import sys, socket, random

def main():

	cx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	cx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	cx.bind(("localhost", 5001))
	cx.listen(20)

	sSock, addr = cx.accept()

	while True:
		result = sSock.recv(512).decode()
		pb = random.randint(1,100)
		if pb<=50:
			print("ACK is lost on the way.")
		else:
			print("ACK is transmitted.")
			sSock.send(b"ACK")

main()
