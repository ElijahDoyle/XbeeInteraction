import mysql.connector
from mysql.connector import Error

def update_parameters(columns, values):
        conn = None
	query = "UPDATE Parameters SET %s = %s"
        try:
                conn = mysql.connector.connect(host= 'localhost', database= 'greenhouse_data', user='root', password = "rJ@mJ@r7")
                cursor = conn.cursor()

                for i in range(0, len(columns)):
                        query = "UPDATE parameters SET " + columns[i] + " = " + str(values[i])
                        cursor.execute(query)

        except Error as e:
                print(e)

        finally:
                if conn != None:
                       conn.commit()
                       conn.close()
                       cursor.close()
        return "successful!"

update_parameters(['minimum_temperature'],[6])
