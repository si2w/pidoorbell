import os,signal,datetime,time,sys,smtplib,threading,pprint
from time import sleep
import piface.pfio as pfio
import refresh_calendar

calendar_overwritten = 0
RUN = True
tmr = None
state = True

def close():
	global RUN
	global tmr
	
	print "close called"

	RUN = False
	if tmr != None:
		tmr.cancel()
		print "Cancel refresh thread"
	else:
		print "Timer Null"
	sys.exit(0)

def rc(): #refesh calendar every 60 seconds
	global calendar_overwritten
	global tmr
	print "refresh calendar" 
	calendar_overwritten = refresh_calendar.refresh_calendar(sys.argv)
	print "result : "+str(calendar_overwritten)
	if RUN == True:
		tmr = threading.Timer(60, rc)
		tmr.start()
	if calendar_overwritten >= 1:
		print "defaults overwritten"

def output(n):
	print "output begin"
	pfio.digital_write(n,1)
	sleep(1)
	pfio.digital_write(n,0)
	sleep(1)
	print "output end"

def email_alert():
	print "email alert begin"
	src = "email@email.com"
	dest = "email@email.com"
	server = smtplib.SMTP('my.smtp.org')
 
	#Send the mail
	msg = "To:" + dest + "\nFrom: " + src + "\nSubject: Dring Dring\n\n" 
	server.sendmail(src, dest, msg)
	server.close()
	print "email sent"

# watch for sigterm signals
signal.signal(signal.SIGINT, close)
signal.signal(signal.SIGTERM, close)
signal.signal(signal.SIGSEGV, close)
signal.signal(signal.SIGILL, close)
signal.signal(signal.SIGABRT, close)
signal.signal(signal.SIGFPE, close)

try:
	# refresh calendar entries in another thread
	rc()
	
	# init pfio board
	pfio.init()

	i = 0

	while(True):
		now = datetime.datetime.now()

		# doorbell pushed ?
		if pfio.digital_read(0) == 1 :
			day_of_week = datetime.datetime.today().weekday()
			hour = now.hour

			if day_of_week >= 5: # Monday is 0 and Sunday is 6
				print "weekend"
				if((hour >= 7 and hour <= 13) or (hour >= 15 and hour <= 20) or calendar_overwritten >= 1):
					output(0)
				else:
					output(1)
					email_alert()
			else:
				print "week"
				if((hour >= 7 and hour <= 20) or calendar_overwritten >= 1):
                                	output(0)
                        	else:
                                	output(1)
					email_alert()
		# door open ?
		#if pfio.digital_read(1) == 0 :
		#	print "open"
		
		# alive led
		if (i % 50) == 0:  
			state = not state
			pfio.digital_write(2,int(state))
		
		# clean power off button
		if pfio.digital_read(2) ==1:
			print "halt PiDoorbell"
			os.system("sudo shutdown -h now")
		
		if i < 100:
			i = i + 1
		else:
			i = 0
except:
	#print "Unexpected error:", sys.exc_info()[0]
	pprint.pprint(sys.exc_info())
	close()
