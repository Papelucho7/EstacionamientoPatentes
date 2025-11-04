import pyodbc
import configparser

def get_connection():
    config = configparser.ConfigParser()
    config.read('config.ini')
    server = config['database']['server']
    database = config['database']['database']

    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            'Trusted_Connection=yes;'
            'TrustServerCertificate=yes;'
        )
        print("✅ Conexión exitosa a SQL Server.")
        return conn

    except pyodbc.Error as e:
        print("❌ Error al conectar a SQL Server:")
        print(e)
        return None



# Ejemplo de uso
if __name__ == "__main__":
    connection = get_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT GETDATE();")
        print("Hora actual del servidor:", cursor.fetchone()[0])
        connection.close()
