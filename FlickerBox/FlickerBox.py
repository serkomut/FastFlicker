import thread
import sys
import time
import websocketclient
from Event import Event
from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer
from websocketclient import create_connection

argc = len(sys.argv)

global_subject = sys.argv[1] if argc > 1 else "a" 
global_port = int(sys.argv[2]) if argc > 2 else 8098
global_QuickTextConnString = "ws://localhost:8099/"


#Todo :
# Send time
# Status sent, read
class FlickerBox(object):

	def __init__(self):
		self.port = global_port
		self.subject = global_subject
		self.QuickTextConnString = global_QuickTextConnString

	def __startClient__(self):
		print "starting client"
		self.client = NotifBoxClient(self.QuickTextConnString,self.subject)
		self.client.subscribeOnMessage(self.__onMessageToClient__)
		self.client.start()
		
	def __startServer__(self):
		print "starting server"
		self.server = SimpleWebSocketServer('', self.port, NotifBoxServer)
		NotifBoxServer.subscribeOnMessage(self.__onMessageToServer__)
		self.server.serveforever()
		
	def __onMessageToClient__(self, msg):
		#TODO Send to client if connected else keep for next time.
		print "Received In Box :", msg
		try :
			NotifBoxServer.messageReceived(msg)
		except Exception,e:
			print str(e)
		
	def __onMessageToServer__(self, subject, msg):		
		print "Received from client to forward :", subject, msg
		self.client.send(subject, msg)
				
	def start(self):
		self.__startClient__()
		self.__startServer__()
		
	
class NotifBoxClient(object):

	def __init__(self, QuickTextConnString,subject):
		self.subject = subject
		self.onMessage = Event()
		self.QuickTextConnString = QuickTextConnString

	def subscribeOnMessage(self, listener):
		self.onMessage.append(listener)
	
	def on_server_message(self, ws, message):
		#print 'New message :', message
		self.onMessage(message)

	def on_server_error(self, ws, error):
		print error

	def on_server_close(self, ws):
		print "### closed ###"
	
	def on_server_open(self, ws):
		print "on_server_open... listening to ", self.subject
		self.textBoxServer.send(self.subject)
		
	def send(self, subject, msg):
		print "Sending message ", msg, " to ", subject
		ws = create_connection(self.QuickTextConnString);
		ws.send(subject)
		ws.send(msg)
		ws.close()
		
	def start(self):
		print "### Starting Client ###"
		self.textBoxServer = websocketclient.WebSocketApp(self.QuickTextConnString,
								on_message = self.on_server_message,
								on_error = self.on_server_error,
								on_close = self.on_server_close)
		self.textBoxServer.on_open = self.on_server_open
		print "### Before thread ###"
		#self.textBoxServer.run_forever()
		thread.start_new_thread(self.textBoxServer.run_forever, ())
		print "### After thread ###"	

class NotifBoxServer(WebSocket):
	#We should have only one instance.
	#If several, it is not a problem not to know where it come from.
	allEvents = Event()
	instance = None
	messageToSend = []
	
	def __init__(self, server, sock, address):
		NotifBoxServer.instance = self
		self.connected = False
		WebSocket.__init__(self, server, sock, address)
	
	@staticmethod
	def subscribeOnMessage(listener):
		NotifBoxServer.allEvents.append(listener)
		
	#client interaction
	#When a client is connected he can send messages like "John@Hello"
	def handleMessage(self):
		if self.data is None:
			self.data = ''		
		try:
			input = str(self.data)
			subject = input.split('@', 1)[0];
			msg = input.split('@', 1)[1];
			self.sendNewMessage(subject,global_subject+' : '+msg)
		except Exception,e:
			print str(e)			

	def sendNewMessage(self, subject, msg):
		print self.address, 'about to send a new message : ', msg, ' to ', subject
		NotifBoxServer.allEvents(subject, msg)	
	
	@staticmethod
	def messageReceived(msg):
		print 'received a new message : ', msg
		if NotifBoxServer.instance is not None and NotifBoxServer.instance.connected :
			NotifBoxServer.instance.sendMessage(msg)
		else :
			NotifBoxServer.messageToSend.append(msg)
		
	def handleConnected(self):
		print self.address, 'connected'
		self.connected = True
		#Send all unread messages
		#Warning, Not thread safe, we should add lock.
		for msg in NotifBoxServer.messageToSend:
			NotifBoxServer.messageReceived(msg)	
		NotifBoxServer.messageToSend = []

	def handleClose(self):
		print self.address, 'closed'
		self.connected = False


box = FlickerBox()
box.start()
#websocketclient.enableTrace(True)
#client = NotifBoxClient("ws://localhost:8099/",'a')
#client.start()
#time.sleep( 5 )
#client.send('ae', 'TG BEAU GOSS')
#time.sleep( 5 )

#server = SimpleWebSocketServer('', 8098, NotifBoxServer)
#server.setServerConfig("ws://localhost:8099/",'a')
#server.serveforever()