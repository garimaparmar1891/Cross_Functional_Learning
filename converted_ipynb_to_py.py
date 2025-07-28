# %%
import pandas as pd
import pyodbc

# %%
server = 'ITT-GARIMA-P\\SQLEXPRESS'
database = 'SalesData'
table = 'sales_data'

conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

conn = None
try:
    conn = pyodbc.connect(conn_str)
    print("Connection to SQL Server successful!")
except Exception as e:
    print(f"Error: Could not connect to SQL Server. Please check your connection details.\n{e}")

# %%
df = None
if conn:
    try:
        query = f"SELECT * FROM {table}"
        df = pd.read_sql(query, conn)
        print(f"Data fetched successfully from table '{table}'!")
        conn.close()
        print("Connection closed.")
    except Exception as e:
        print(f"Error fetching data: {e}")
else:
    print("Cannot fetch data, connection not established.")

# %%
print(df.head())

# %%
def get_category(product_name):
    if not isinstance(product_name, str):
        return 'Other'
    product_name = product_name.lower()
    if 'iphone' in product_name or 'google phone' in product_name or 'vareebadd phone' in product_name:
        return 'Phone'
    elif 'headphones' in product_name or 'airpods' in product_name:
        return 'Audio'
    elif 'cable' in product_name or 'charger' in product_name or 'batteries' in product_name:
        return 'Accessory'
    elif 'laptop' in product_name or 'monitor' in product_name:
        return 'Computer & Display'
    else:
        return 'Other'

def get_zipcode(address):
    try:
        return address.split(',')[-1].strip().split(' ')[-1]
    except (IndexError, AttributeError):
        return None


# %%
def remove_duplicates(df):
    return df.drop_duplicates()

def handle_missing(df, required_cols):
    return df.dropna(subset=required_cols)

def convert_types(df, quantity_col, price_col, date_col):
    df[quantity_col] = pd.to_numeric(df[quantity_col], errors='coerce')
    df[price_col] = pd.to_numeric(df[price_col], errors='coerce')
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    return df

def enrich_time_data(df, date_col):
    df['Hour'] = df[date_col].dt.hour
    df['DayOfWeek'] = df[date_col].dt.day_name()
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month
    return df

def calculate_sales(df, quantity_col, price_col):
    df['Sales'] = df[quantity_col] * df[price_col]
    return df

def extract_location_details(df, address_col):
    df['City'] = df[address_col].apply(lambda x: x.split(',')[1].strip() if pd.notnull(x) and len(x.split(',')) > 1 else None)
    df['State'] = df[address_col].apply(lambda x: x.split(',')[2].split()[0] if pd.notnull(x) and len(x.split(',')) > 2 else None)
    df['ZipCode'] = df[address_col].apply(get_zipcode)
    return df

def categorize_products(df):
    df['Category'] = df['Product'].apply(get_category)
    return df


# %%
def clean_data(df):
    df = df.copy()

    quantity_col = 'Quantity'
    price_col = 'Price'
    date_col = 'OrderDate'
    address_col = 'Address'

    df = remove_duplicates(df)
    df = handle_missing(df, [quantity_col, price_col, date_col])
    df = convert_types(df, quantity_col, price_col, date_col)
    df = enrich_time_data(df, date_col)
    df = calculate_sales(df, quantity_col, price_col)
    df = extract_location_details(df, address_col)
    df = categorize_products(df)

    print("Data cleaning and transformations complete.")
    return df


# %%
if df is not None:
    df_cleaned = clean_data(df)
else:
    print("DataFrame is empty. Cannot perform transformations.")


# %%
df_cleaned['OrderID'] = df_cleaned['OrderID'].astype(str)
df_cleaned['Product'] = df_cleaned['Product'].astype(str)
df_cleaned['Quantity'] = pd.to_numeric(df_cleaned['Quantity'], errors='coerce').astype('Int64')
df_cleaned['Price'] = pd.to_numeric(df_cleaned['Price'], errors='coerce')
df_cleaned['OrderDate'] = pd.to_datetime(df_cleaned['OrderDate'], errors='coerce')
df_cleaned['Address'] = df_cleaned['Address'].astype(str)
df_cleaned['Hour'] = pd.to_numeric(df_cleaned['Hour'], errors='coerce').astype('Int64')
df_cleaned['Sales'] = pd.to_numeric(df_cleaned['Sales'], errors='coerce')
df_cleaned['DayOfWeek'] = df_cleaned['DayOfWeek'].astype(str)
df_cleaned['Year'] = pd.to_numeric(df_cleaned['Year'], errors='coerce').astype('Int64')
df_cleaned['ZipCode'] = df_cleaned['ZipCode'].astype(str)
df_cleaned['Category'] = df_cleaned['Category'].astype(str)
df_cleaned['Month'] = pd.to_numeric(df_cleaned['Month'], errors='coerce').astype('Int64')
df_cleaned['City'] = df_cleaned['City'].astype(str)
df_cleaned['State'] = df_cleaned['State'].astype(str)

# %%
df_cleaned = df_cleaned.sort_values('OrderDate')
df_cleaned['CumulativeSales'] = df_cleaned['Sales'].cumsum()

# %%
df_cleaned['Rolling7DaySales'] = df_cleaned['Sales'].rolling(window=7, min_periods=1).sum()

# %%
region_map = {
    'CA': 'West', 'NY': 'Northeast', 'FL': 'South', 'TX': 'South'
}
df_cleaned['Region'] = df_cleaned['State'].map(region_map)

# %%
bins = [0, 1000, 5000, 10000, df_cleaned['Sales'].max()]
labels = ['Low', 'Medium', 'High', 'Very High']
df_cleaned['OrderValueCategory'] = pd.cut(df_cleaned['Sales'], bins=bins, labels=labels)

# %%
order_counts = df_cleaned.groupby('OrderID')['Product'].count()
df_cleaned['IsBundle'] = df_cleaned['OrderID'].map(lambda x: order_counts[x] > 1)

# %%
def get_season(month):
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    else:
        return 'Fall'
df_cleaned['Season'] = df_cleaned['Month'].apply(get_season)

# %%
print(df_cleaned.head())

# %% [markdown]
# Loading cleaned data in ssms

# %%
import pyodbc
import pandas as pd


conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=ITT-GARIMA-P\\SQLEXPRESS;'
    'DATABASE=SalesData;'
    'Trusted_Connection=yes;'
)

cursor = conn.cursor()

# %%
df_cleaned = df_cleaned.dropna().reset_index(drop=True)


# %%
table_name = 'SalesData_Cleaned'


# %%
check_table_sql = f"""
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_NAME = '{table_name}'
)
BEGIN
    CREATE TABLE {table_name} (
        {', '.join([
            f"[{col}] " + (
                'INT' if str(dtype) == 'int64' else
                'FLOAT' if str(dtype) == 'float64' else
                'DATETIME' if str(dtype).startswith('datetime') else
                'BIT' if str(dtype) == 'bool' else
                'NVARCHAR(MAX)'
            )
            for col, dtype in df_cleaned.dtypes.items()
        ])}
    );
END
"""
cursor.execute(check_table_sql)
conn.commit()

cursor.execute(f"TRUNCATE TABLE {table_name}")
conn.commit()


# %%
import os

current_dir = os.getcwd()
output_folder = os.path.join(current_dir, 'inserting_data')
os.makedirs(output_folder, exist_ok=True)

csv_file_path = os.path.join(output_folder, f"{table_name}.csv")
df_cleaned.to_csv(csv_file_path, index=False)

print(f"Cleaned data saved to CSV at: {csv_file_path}")

# %%
cols = ', '.join(f'[{col}]' for col in df_cleaned.columns)
placeholders = ', '.join(['?' for _ in df_cleaned.columns])
insert_sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"

for _, row in df_cleaned.iterrows():
    cursor.execute(insert_sql, tuple(row))

conn.commit()
cursor.close()
conn.close()
print("Table truncated and new data inserted.")


# %% [markdown]
# Data Visualizations

# %%
import plotly.express as px
import calendar

monthly_sales_by_year = df_cleaned.groupby(['Year', 'Month'])['Sales'].sum().reset_index()
monthly_sales_by_year = monthly_sales_by_year.sort_values(['Year', 'Month'])
monthly_sales_by_year['MonthName'] = monthly_sales_by_year['Month'].apply(lambda x: calendar.month_abbr[int(x)])

monthly_sales_by_year['Year'] = monthly_sales_by_year['Year'].astype(str)

fig = px.line(monthly_sales_by_year, 
              x='MonthName', 
              y='Sales', 
              color='Year',
              title='Total Sales per Month by Year',
              labels={'MonthName': 'Month', 'Sales': 'Total Sales ($)', 'Year': 'Year'},
              markers=True)

fig.update_traces(hovertemplate='<b>Month:</b> %{x}<br><b>Sales:</b> $%{y:,.2f}')
fig.update_layout(
    xaxis_title='Month',
    yaxis_title='Total Sales ($)',
    title_x=0.5,
    xaxis={'categoryorder':'array', 'categoryarray': [calendar.month_abbr[i] for i in range(1, 13)]}
)
fig.show()

# %%
import plotly.graph_objects as go
import calendar

monthly_category_sales = df_cleaned.groupby(['Month', 'Category'])['Sales'].sum().reset_index()

months = sorted(monthly_category_sales['Month'].unique())
month_names = [calendar.month_abbr[int(m)] for m in months]

fig = go.Figure()

for month in months:
    df_month = monthly_category_sales[monthly_category_sales['Month'] == month]
    fig.add_trace(
        go.Bar(
            x=df_month['Category'],
            y=df_month['Sales'],
            name=calendar.month_abbr[int(month)],
            visible=False
        )
    )

total_category_sales = df_cleaned.groupby('Category')['Sales'].sum().reset_index()
fig.add_trace(
    go.Bar(
        x=total_category_sales['Category'],
        y=total_category_sales['Sales'],
        name='All Months',
        visible=True
    )
)

fig.update_traces(
    texttemplate='$%{y:,.2s}', 
    textposition='inside',
    textfont=dict(
        color='white',
        size=12
    ),
    insidetextanchor='end',
    selector=dict(type='bar')
)

buttons = []

buttons.append(dict(
    label="All Months",
    method="update",
    args=[{"visible": [False]*len(months) + [True]},
          {"title": "Total Sales by Product Category (All Months)"}]
))

for i, month_name in enumerate(month_names):
    visibility = [False] * (len(months) + 1)
    visibility[i] = True
    buttons.append(dict(
        label=month_name,
        method="update",
        args=[{"visible": visibility},
              {"title": f"Total Sales by Category for {month_name}"}]
    ))

fig.update_layout(
    updatemenus=[
        dict(
            active=0,
            buttons=buttons,
            direction="down",
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0.1,
            xanchor="left",
            y=1.15,
            yanchor="top"
        )
    ],
    title_text="Total Sales by Product Category",
    xaxis_title="Product Category",
    yaxis_title="Total Sales ($)",
    title_x=0.5
)

fig.show()

# %%
top_products = df_cleaned.groupby('Product')['Quantity'].sum().nlargest(10).reset_index()

fig = px.bar(top_products, 
             x='Quantity', 
             y='Product', 
             orientation='h',
             title='Top 10 Selling Products by Quantity',
             labels={'Quantity': 'Total Quantity Sold', 'Product': 'Product'})
fig.update_layout(yaxis={'categoryorder':'total ascending'})
fig.show()

# %%
city_sales = df_cleaned[df_cleaned['City'] != 'None'].groupby('City')['Sales'].sum().nlargest(10).reset_index()

fig = px.bar(city_sales, 
             x='Sales', 
             y='City', 
             orientation='h',
             title='Top 10 Cities by Sales',
             labels={'Sales': 'Total Sales ($)', 'City': 'City'},
             text='Sales')
fig.update_traces(texttemplate='$%{text:,.2s}')
fig.update_layout(yaxis={'categoryorder':'total ascending'})
fig.show()

# %%
hourly_orders = df_cleaned.groupby('Hour')['OrderID'].count().reset_index()

fig = px.line(hourly_orders, 
              x='Hour', 
              y='OrderID', 
              title='Number of Orders per Hour',
              labels={'Hour': 'Hour of Day', 'OrderID': 'Number of Orders'},
              markers=True)
fig.update_xaxes(dtick=1)
fig.show()

# %%
fig = px.treemap(df_cleaned, 
                 path=[px.Constant("All Sales"), 'Category', 'Product'], 
                 values='Sales',
                 title='Sales Treemap by Category and Product',
                 hover_data=['Quantity'])
fig.update_traces(textinfo="label+percent entry")
fig.show()
