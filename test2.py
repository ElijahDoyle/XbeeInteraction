import mysql.connector
from mysql.connector import Error

def get_parameters():
        conn = None
        data = {}
        try:
                conn = mysql.connector.connect(host='localhost', database='greenhouse_data', user='root', password='rJ@mJ@r7')
                cursor = conn.cursor()
                query = "SELECT * FROM parameters"
                cursor.execute(query)
                parameters = cursor.fetchone()

                data["min_temp"] = str(parameters[0])
                data["max_temp"] = str(parameters[1])
                data["fert_water_conductivity"] = str(parameters[2])
                data["hydro_duration"] = str(parameters[3])
                data["hydro_freqency"] = str(parameters[4])
        except Error as e:
                print(e)

        finally:
                conn.close()
                cursor.close()
                return data
print(get_parameters())
