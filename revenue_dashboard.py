import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# โหลดข้อมูล
df = pd.read_csv("merged_data_with_fields.csv")

# เตรียมข้อมูล
df['Total price'] = df['Total price'].replace('[^\\d.]', '', regex=True).astype(float)
df['Booked At'] = pd.to_datetime(df['Booked At'])
df['Check - In'] = pd.to_datetime(df['Check - In'])
df['Month'] = df['Check - In'].dt.to_period('M')
df = df[df['Booking status'] == 'Booked']
df['Room Type'] = df['Room_room']
df['Month_str'] = df['Check - In'].dt.strftime('%Y-%m')

# ความสัมพันธ์ระหว่างราคาและรายได้รวม
revenue_by_price = df.groupby('Total price')['Total price'].agg(['count', 'sum']).reset_index()
revenue_by_price.columns = ['Price', 'Bookings', 'Total Revenue']
revenue_by_price_sorted = revenue_by_price.sort_values('Price')

# ราคาที่แนะนำ (median) และราคาปัจจุบัน (เฉลี่ย)
recommended_prices = df.groupby(['Room Type', 'Month_str'])['Total price'].median().reset_index()
recommended_prices.columns = ['Room Type', 'Month', 'Recommended Price']
current_prices = df.groupby(['Room Type', 'Month_str'])['Total price'].mean().reset_index()
current_prices.columns = ['Room Type', 'Month', 'Current Price']
price_comparison = pd.merge(current_prices, recommended_prices, on=['Room Type', 'Month'])

# เริ่มแสดงผลใน Streamlit
st.title("📊 Revenue Optimization Dashboard")

st.header("📈 ความสัมพันธ์ระหว่างราคาและรายได้รวม")
fig1 = px.scatter(revenue_by_price_sorted, x="Price", y="Total Revenue", size="Bookings",
                  labels={"Price": "ราคาห้องพัก", "Total Revenue": "รายได้รวม"},
                  title="ความสัมพันธ์ระหว่างราคาและรายได้")
st.plotly_chart(fig1)

st.header("📊 ช่วงราคาที่เหมาะสมต่อเดือนแยกตามประเภทห้อง")
fig2 = px.box(df, x="Month_str", y="Total price", color="Room Type", points="all",
              labels={"Month_str": "เดือน", "Total price": "ราคาห้อง"},
              title="ช่วงราคาต่อเดือนแยกตามประเภทห้อง")
st.plotly_chart(fig2)

st.header("📉 เปรียบเทียบราคาปัจจุบันกับราคาที่แนะนำ")
room_types = df['Room Type'].unique()
selected_room = st.selectbox("เลือกประเภทห้อง", room_types)

filtered_comparison = price_comparison[price_comparison["Room Type"] == selected_room]
fig3 = px.bar(filtered_comparison, x="Month", y=["Current Price", "Recommended Price"],
              barmode="group",
              color_discrete_sequence=["#636EFA", "#EF553B"],
              labels={"value": "ราคา", "Month": "เดือน", "variable": "ประเภท"},
              title=f"ราคาปัจจุบัน vs ราคาที่แนะนำ: {selected_room}")
st.plotly_chart(fig3)

st.header("🧪 เครื่องมือจำลองสถานการณ์")
month_options = df[df['Room Type'] == selected_room]['Month_str'].unique()
selected_month = st.selectbox("เลือกเดือน", sorted(month_options))

recommended = recommended_prices[
    (recommended_prices['Room Type'] == selected_room) & 
    (recommended_prices['Month'] == selected_month)
]['Recommended Price'].values[0]

input_price = st.slider("ปรับราคาห้อง", 500.0, 5000.0, float(recommended), step=10.0)

# สมมุติฐาน: รายได้ = ราคา * จำนวนจองที่ลดลงตาม gdp elasticity
elasticity = -1.2  # ความยืดหยุ่นของราคา
base_bookings = df[
    (df['Room Type'] == selected_room) & 
    (df['Month_str'] == selected_month)
].shape[0]

price_ratio = input_price / recommended
simulated_bookings = base_bookings * (price_ratio ** elasticity)
simulated_revenue = input_price * simulated_bookings

st.markdown(f"""
### 🔍 ผลลัพธ์การจำลอง
- **จำนวนการจองที่คาดการณ์:** {simulated_bookings:.0f} ครั้ง
- **รายได้รวมที่คาดการณ์:** THB {simulated_revenue:,.2f}
""")
