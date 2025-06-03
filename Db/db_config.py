import mysql.connector

def get_db_cursor():
    db_config = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345678",
        database="ProyectoF",
        port=3306
    )
    print("Conexión a la base de datos establecida correctamente.")
    mycursor = db_config.cursor()
    return mycursor, db_config




