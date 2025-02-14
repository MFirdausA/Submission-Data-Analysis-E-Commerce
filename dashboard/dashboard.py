import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

st.set_page_config(page_title="Order Analysis Dashboard", layout="wide")

# load data
@st.cache_data
def load_data():
    data_path = Path(__file__).parent.parent / "data"
    
    orders_df = pd.read_csv(data_path / 'orders_dataset.csv')
    customers_df = pd.read_csv(data_path / 'customers_dataset.csv')
    orders_items_df = pd.read_csv(data_path / 'order_items_dataset.csv')
    products_df = pd.read_csv(data_path / 'products_dataset.csv')
    product_category_name_translation_df = pd.read_csv(data_path / 'product_category_name_translation.csv')
    
    orders_df['order_purchase_timestamp'] = pd.to_datetime(orders_df['order_purchase_timestamp'])
    
    return orders_df, customers_df, orders_items_df, products_df, product_category_name_translation_df

try:
    # Load data
    orders_df, customers_df, orders_items_df, products_df, product_category_name_translation_df = load_data()

    # filters
    st.sidebar.header("Filters")
    
    # Date range selector
    min_date = orders_df['order_purchase_timestamp'].dt.date.min()
    max_date = orders_df['order_purchase_timestamp'].dt.date.max()
    
    selected_dates = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Check start and end dates selected
    if len(selected_dates) != 2:
        st.error("Please select a date range (start and end dates).")
        st.stop()
    
    start_date, end_date = selected_dates

    # Filter orders by date range
    filtered_orders = orders_df[
        (orders_df['order_purchase_timestamp'].dt.date >= start_date) &
        (orders_df['order_purchase_timestamp'].dt.date <= end_date)
    ]

    # Header
    st.title("E-commerce Order Analysis Dashboard")
    st.write(f"Analysis of orders from {start_date} to {end_date}")

    # Create two columns
    col1, col2 = st.columns(2)

    with col1:
        st.header("Top Cities by Order Count")
        
        # Calculate top citys
        orders_with_city = filtered_orders.merge(customers_df, on='customer_id', how='left')
        top_cities = orders_with_city['customer_city'].value_counts().head(10)

        fig1, ax1 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_cities.index, y=top_cities.values, ax=ax1, color="lightblue")
        
        ax1.set_title(f"Top 10 Cities by Order Count ({start_date} to {end_date})")
        ax1.set_xlabel("City")
        ax1.set_ylabel("Number of Orders")
        ax1.set_xticklabels(top_cities.index, rotation=45)
        
        st.pyplot(fig1)

    with col2:
        st.header("Top Product Categories by City")
        
        # load data for category analysis
        merged_df = orders_items_df.merge(products_df, on='product_id', how='left')
        merged_df = merged_df.merge(filtered_orders[['order_id', 'customer_id']], on='order_id', how='left')
        merged_df = merged_df.merge(customers_df[['customer_id', 'customer_city']], on='customer_id', how='left')
        merged_df = merged_df.merge(product_category_name_translation_df, on='product_category_name', how='left')
        merged_df = merged_df[['order_id', 'customer_city', 'product_category_name_english']]

        top_category_per_city = merged_df.groupby(['customer_city', 'product_category_name_english'])['order_id'].count().reset_index()
        top_category_per_city = top_category_per_city.rename(columns={'order_id': 'total_orders'})
        top_category_per_city = top_category_per_city.sort_values(by=['customer_city', 'total_orders'], ascending=[True, False])
        top_category_per_city = top_category_per_city.loc[top_category_per_city.groupby('customer_city')['total_orders'].idxmax()]
        top_category_per_city = top_category_per_city.sort_values(by='total_orders', ascending=False)

        # Get city 10 top
        top_10_cities = top_category_per_city['customer_city'].head(10)
        top_10_data = top_category_per_city[top_category_per_city['customer_city'].isin(top_10_cities)]

        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_10_data['customer_city'], y=top_10_data['total_orders'], 
                    hue=top_10_data['product_category_name_english'], dodge=False, ax=ax2)
        
        ax2.set_title(f"Most Popular Product Category per City ({start_date} to {end_date})")
        ax2.set_xlabel("City")
        ax2.set_ylabel("Number of Orders")
        ax2.set_xticklabels(top_10_data['customer_city'], rotation=45)
        ax2.legend(title='Product Category', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        st.pyplot(fig2)

    st.header("Key Metrics")
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

    with metrics_col1:
        total_orders = len(filtered_orders)
        st.metric("Total Orders", f"{total_orders:,}")

    with metrics_col2:
        total_cities = orders_with_city['customer_city'].nunique()
        st.metric("Total Cities", f"{total_cities:,}")

    with metrics_col3:
        avg_orders_per_city = total_orders / total_cities if total_cities > 0 else 0
        st.metric("Average Orders per City", f"{avg_orders_per_city:.1f}")

    # Add data tables
    st.header("Detailed Data")
    
    if st.checkbox("Show Top Cities Data"):
        st.write("Top 10 Cities by Order Count")
        st.dataframe(pd.DataFrame({
            'City': top_cities.index,
            'Number of Orders': top_cities.values
        }))

    if st.checkbox("Show Top Categories Data"):
        st.write("Most Popular Categories by City")
        st.dataframe(top_10_data)

except FileNotFoundError as e:
    st.error("""
        Error: Unable to load data files. Please check the following:
        1. Make sure the 'data' folder exists in the root directory.
        2. Verify that all data files exist in the 'data' directory:
           - orders_dataset.csv
           - customers_dataset.csv
           - order_items_dataset.csv
           - products_dataset.csv
           - product_category_name_translation.csv
    """)
    st.exception(e)
except Exception as e:
    st.error("An unexpected error occurred while loading or processing the data.")
    st.exception(e)