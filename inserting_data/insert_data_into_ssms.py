import pandas as pd
import pyodbc

df = pd.read_csv('inserting_data/sample_sales_data.csv')

server = 'ITT-GARIMA-P\SQLEXPRESS'       
database = 'SalesData'   
driver = '{ODBC Driver 17 for SQL Server}'  

conn = pyodbc.connect(
    f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
)
cursor = conn.cursor()

cursor.execute("IF OBJECT_ID('dbo.sales_data', 'U') IS NOT NULL DROP TABLE dbo.sales_data")
conn.commit()

create_table_query = '''
CREATE TABLE dbo.sales_data (
    OrderID NVARCHAR(255),
    Product NVARCHAR(255),
    Quantity NVARCHAR(255),
    Price NVARCHAR(255),
    OrderDate NVARCHAR(255),
    Address NVARCHAR(255)
)
'''
cursor.execute(create_table_query)
conn.commit()

for index, row in df.iterrows():
    cursor.execute('''
        INSERT INTO dbo.sales_data (OrderID, Product, Quantity, Price, OrderDate, Address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', str(row['Order ID']), str(row['Product']), str(row['Quantity Ordered']), str(row['Price Each']),
         str(row['Order Date']), str(row['Purchase Address']))
conn.commit()

cursor.close()
conn.close()
print("Data imported successfully!")
