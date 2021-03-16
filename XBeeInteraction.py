import mysql.connector
from mysql.connector import Error
from datetime import datetime
import serial
import time

time.sleep(5)

# intitiallizes the serial object with the connected XBee (the filepath may change depending on the port used)
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=12)

def sendMessage(message, serialObject):
	bytesSent = serialObject.write(message.encode('utf-8'))
#	print(bytesSent)

#this function retrieves the current parameters from the database
def get_parameters():
	conn = None
	data = {}
	try:
		conn = mysql.connector.connect(host='localhost', database='greenhouse_data', user='root', password='rJ@mJ@r7')
		cursor = conn.cursor()
		query = "SELECT parameter, value FROM parameters"
		cursor.execute(query)

		row = cursor.fetchone()
		while row is not None:
			data[row[0]] = str(row[1])
			row = cursor.fetchone()

	except Error as e:
		print(e)
		return(e)

	finally:
		conn.close()
		cursor.close()
		# remember that data is a dictionary
		return data

def get_status(component):
	query = "select status from status where component = \'" + component +"\'"
	conn = None
	status = None
	try:
		conn = mysql.connector.connect(host='localhost', database='greenhouse_data', user='root', password='rJ@mJ@r7')
		cursor = conn.cursor(buffered=True)
		row = cursor.execute(query)
		status = str(cursor.fetchone()[0])
	except Error as e:
		return(e)
	finally:
		conn.close()
		cursor.close()
		return status

# this function returns the current manual control settings from the database
def get_manual_controls():
	conn = None
	data = {}
	try:
		conn = mysql.connector.connect(host='localhost', database='greenhouse_data', user='root', password='rJ@mJ@r7')
		cursor = conn.cursor(buffered=True)

		query = "Select system, status from manual_controls"

		cursor.execute(query)
		row = cursor.fetchone()
		while row is not None:
			data[row[0]] = row[1]
			row = cursor.fetchone()

	except Error as e:
		print(e)
	finally:
		conn.close()
		cursor.close()
		return data

# this function updates the status of a given component
def update_status(component, status):
	conn = None
	debug = "good"
	try:
		conn = mysql.connector.connect(host='localhost', database='greenhouse_data', user='root', password='rJ@mJ@r7')
		cursor = conn.cursor()

		query = "UPDATE status SET status = \'" + status + "\' WHERE component = \'" + component + "\'"
		cursor.execute(query)

	except Error as e:
		debug = str(e)

	finally:
		conn.commit()
		conn.close()
		cursor.close()
		return debug

# this function inserts environmental data and a timestamp into the table
def insert_env_data(table, type, value):
    conn = None
    debug = "Start"
    try:
        conn = mysql.connector.connect(host='localhost', database='greenhouse_data', user='root', password='rJ@mJ@r7')
        cursor = conn.cursor()
        query = "INSERT INTO " + table + " (" + type +", time_recieved) Values ("+ str(value) + ", current_timestamp)"
        debug = query
        cursor.execute(query)
        debug = "Done"
    except Error as e:
        debug = str(e)

    finally:
        conn.commit()
        conn.close()
        cursor.close()
        return debug

def createRequest(target):
	request = ""
	parameters = get_parameters()
	manualControls = get_manual_controls()

	# if target is 1, it creates a request for Zach's arduino
	if target==1:
		request += "1"
		minTemp = parameters["minimum_temperature"]
		maxTemp = parameters["maximum_temperature"]
		request += "m:" + str(minTemp)
		request += "M:" + str(maxTemp)
		bigFan = manualControls["big_fan"]
		smallFan = manualControls["little_fan"]
		heatPump = manualControls["water_heat"]
		vents = manualControls["vents"]
		request += "b:" + str(bigFan) + "s:" + str(smallFan)
		request += "h:" + str(heatPump) + "v:" + str(vents)

	# if the target is 2 it creates a request for matt's arduino
	else:
		request += "2"
		minCond =  str(parameters["minimum_conductivity"])
		maxCond = str(parameters["maximum_conductivity"])
		hyDuration = str(parameters["hydroponics_duration"])
		hyFrequency = str(parameters["hydroponics_frequency"])
		constant = parameters["constant_hydroponics"]
		request += "m:" + minCond + "M:" + maxCond
		request += "d:" + hyDuration + "f:" + hyFrequency
		request += "c:" + constant
		tubNum = str(manualControls["twoTubs"])
		pause = str(manualControls["water_fertilizer"])
		irPump = str(manualControls["irrigation_pump"])
		p1 = str(manualControls["pump1"])
		p2 = str(manualControls["pump2"])
		p3 = str(manualControls["pump3"])
		request += "t:" + tubNum + "p:" + pause
		request += "i:" + irPump + "1:"+ p1
		request += "2:" + p2 + "3:" + p3

	return request

def handleResponse(response):
	if response[0] == "1":
		responses = response.split(" ")
		for r in responses:
			# humidity
			if r[0] == "h":
				data = r[2:]
				insert_env_data("humidity", "humidity", data)
			# average inside temp
			elif r[0] == "a":
				data = r[2:]
				insert_env_data("inside_temperature", "temperature", data)
			# front temperature
			elif r[0] == "f":
				data = r[2:]
				insert_env_data("front_temp", "temperature", data)
			# middle temperature
			elif r[0] == "m":
				data = r[2:]
				insert_env_data("middle_temp","temperature", data)
			# back temperature
			elif r[0] == "b":
				data = r[2:]
				insert_env_data("back_temp", "temperature", data)
			# outside temperature
			elif r[0] == "o":
				data = r[2:]
				insert_env_data("outside_temperature", "temperature", data)
			# ground temperature
			elif r[0] == "g":
				data = r[2:]
				insert_env_data("ground_temp", "temperature", data)
			# mulch temperature
			elif r[0] == "p":
				data = r[2:]
				insert_env_data("mulch_temperature", "temperature", data)
			# mulch water temperature
			elif r[0] == "w":
				data = r[2:]
				insert_env_data("mulch_water_temp", "temperature", data)

	elif response[0] == "2":
		responses = response.split(" ")
		for r in responses:
			# electrical conductivity
			if r[0] == "c":
				data = r[2:]
				insert_env_data("fertilized_water_conductivity", "conductivity", data)
			# IBC tote temperature
			elif r[0] == "t":
				data = r[2:]
				insert_env_data("IBC_temperature", "temperature", data)
			# fertilizer tub status
			elif r[0] == "F":
				data = r[2]
				if data  == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Fertilizer Tub", status)
			# water tub status
			elif r[0] == "W":
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Water Tub", status)
			# calcium tub status
			elif r[0] == "C":
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Calcium Tub", status)
			# status of sump pump
			elif r[0] == "s":
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Sump Pump", status)
			# status of pump 1
			elif r[0] == "1":
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Pump1", status)
			# status of pump 2
			elif r[0] == "2" and len(r)>1:
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Pump2", status)
			# status of pump 3
			elif r[0] == "3":
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Pump3", status)
			# status of conductivity sensor
			elif r[0] == "S":
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Conductivity Sensor", status)
			# status of battery packs
			elif r[0] == "B" or r[0] == "b":
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Battery Packs", status)
			# status of Distance sensors
			elif r[0] == "D" or r[0] == "d":
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Distance Sensors", status)
			# status of temperature sensor
			elif r[0] == "T":
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Temperature Sensor", status)
			# status of Irrigation pump
			elif r[0] == "I":
				data = r[2]
				if data == "1":
					status = "Operational"
				else:
					status = "Needs Maintenance"
				update_status("Irrigation Pump", status)
			# status of IBC temp
			elif r[0] == "i":
				data = r[2]
				if data == "1":
					status = "Safe"
				else:
					status = "Unsafe"
				update_status("IBC Temperature", status)


#================================  TESTING CODE  ===============

#testResponseZ = "1 h:.45 a:70.5 f:71.5 b:69.5 m:70.5 o:68.9 g:65.4 p:100.5 w:95.5 ~"
#testResponse = "2 c:1.50 t:45.50 F:0 W:0 C:0 s:0 1:0 2:0 3:0 I:0 S:0 T:0 D:0 d:0 B:0 b:0 i:0 ~"
#print(testResponse.split(" "))
#handleResponse(testResponseZ)


#message = createRequest(2)
#print((message))
#sendMessage(message, ser)

#print(update_status("Fertilizer Tub", "Needs Maintenance", True))


listening = False
while listening:
	incoming = ser.read_until("~".encode('utf-8'))
	if len(incoming) > 1:
		response = str(incoming.decode())
#		handleResponse(response)
#		responses = response.split(" ")
#		for r in responses:
#			print(r)
		print(response)
		listening = False

#print(update_status("Water Tub", "Operational"))
#print(insert_env_data("inside_temperature", 63))
#print(get_status("Pump3"))

#================================  MAIN LOOP  =================

# the cycles variable will keep track of how many cycles have been made since the last database update
cycles = 0
# the database will be updated after *this* many cycles
updateDelay = 45

# this variable keeps the loop running
running = True
while running:
	ser.flushInput()
	ser.flushOutput()

	# request/response handling of zach's arduino
	request1 = createRequest(1) #change back to oa 1
	sendMessage(request1, ser)
	print(request1)
	incoming = ser.read_until("~".encode('utf-8'))
	response1 = str(incoming.decode())
#	print(response1)
	if response1 == "":
		print("empty")
		empty = True
	else:
		print(response1)
		empty = False
	if not empty and (cycles==0 or cycles==5) and response1[0] == "1" :
		print("updating")
		handleResponse(response1)

	# wait 5 seconds after
	time.sleep(5)
	ser.flushInput()
	ser.flushOutput()

#	print(request1)

	# request/response handling of matt's arduino
	request2 = createRequest(2)
	print(request2)
	sendMessage(request2, ser)
	incoming = ser.read_until("~".encode('utf-8'))
	response2 = str(incoming.decode())
	if response2 == "":
		empty = True
		print("no response")
	else:
		print (response2)
		empty = False
	if not empty and (cycles == 0 or cycles == 5) and response2[0]=="2":
		handleResponse(response2)
		print("updated")
	#print(request2)
	# wait another 5 seconds
	time.sleep(5)

	if cycles >= updateDelay:
		cycles = 0
	else:
		cycles += 1
	print(cycles)
	# this cycle has finished and the loop will go again



