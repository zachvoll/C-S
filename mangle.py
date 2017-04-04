import sys, random, time

def main():
	packet = ""
	for i in range(512):
		packet += "a" # Make a packet.
	while 1:
		mangledpacket = replace(packet, 2, 20, 20) # The first parameter is the packet. The second is the delay. The third and fourth are probabilities for dropping and mangling.
		print(mangledpacket);

def replace(s, delay, drop, mangle):
	time.sleep(delay)
	result = ""
	if len(s) < 512:
		return result
	prob = random.randint(0,100)
	if prob < drop + mangle:
		if prob < drop:
			return result
		else:
			for i in range(512):
				result = result + str(chr(random.randint(32,126)))
			return result
	else:
		return s

main()
