from influxdb import InfluxDBClient

host = 'localhost'
port = 8086
user = 'root'
password = 'root'
dbname = 'mydb'
myclient = InfluxDBClient(host, port, user, password, dbname)


myclient.drop_database(dbname)
# Uncomment the following code if the database is not yet created
# myclient.create_database(dbname)
# myclient.create_retention_policy('awesome_policy', '3d', 3, default=True)