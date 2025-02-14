import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Set page configuration
st.set_page_config(page_title="Order Analysis Dashboard", layout="wide")

# Function to load data
@st.cache_data
def load_data():
    data_path = '../data'
    
    orders_df = pd.read_csv(os.path.join(data_path, 'orders_dataset.csv'))
    customers_df = pd.read_csv(os.path.join(data_path, 'customers_dataset.csv'))
    orders_items_df = pd.read_csv(os.path.join(data_path, 'order_items_dataset.csv'))
    products_df = pd.read_csv(os.path.join(data_path, 'products_dataset.csv'))
    product_category_name_translation_df = pd.read_csv(os.path.join(data_path, 'product_category_name_translation.csv'))
    
    orders_df['order_purchase_timestamp'] = pd.to_datetime(orders_df['order_purchase_timestamp'])
    
    return orders_df, customers_df, orders_items_df, products_df, product_category_name_translation_df

try:
    # Load data
    orders_df, customers_df, orders_items_df, products_df, product_category_name_translation_df = load_data()

    # Header
    st.title("E-commerce Order Analysis Dashboard")
    st.write("Analysis of orders and product categories across different cities")

    # Create two columns
    col1, col2 = st.columns(2)

    with col1:
        st.header("Top Cities by Order Count")
        
        # Calculate top cities
        latest_year = orders_df['order_purchase_timestamp'].dt.year.max()
        recent_orders = orders_df[orders_df['order_purchase_timestamp'].dt.year == latest_year]
        orders_with_city = recent_orders.merge(customers_df, on='customer_id', how='left')
        top_cities_last_year = orders_with_city['customer_city'].value_counts().head(10)
        
        # Create figure using graph_objects
        fig1 = go.Figure(data=[
            go.Bar(
                x=top_cities_last_year.index,
                y=top_cities_last_year.values,
                marker_color='lightblue'
            )
        ])
        
        fig1.update_layout(
            title=f"Top 10 Cities by Order Count in {latest_year}",
            xaxis_title="City",
            yaxis_title="Number of Orders",
            xaxis_tickangle=-45,
            height=500
        )
        
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.header("Top Product Categories by City")
        
        # Prepare data for category analysis - following your original analysis
        merged_df = orders_items_df.merge(products_df, on='product_id', how='left')
        merged_df = merged_df.merge(orders_df[['order_id', 'customer_id']], on='order_id', how='left')
        merged_df = merged_df.merge(customers_df[['customer_id', 'customer_city']], on='customer_id', how='left')
        merged_df = merged_df.merge(product_category_name_translation_df, on='product_category_name', how='left')
        merged_df = merged_df[['order_id', 'customer_city', 'product_category_name_english']]

        # Calculate top category per city
        top_category_per_city = merged_df.groupby(['customer_city', 'product_category_name_english'])['order_id'].count().reset_index()
        top_category_per_city = top_category_per_city.rename(columns={'order_id': 'total_orders'})
        top_category_per_city = top_category_per_city.sort_values(by=['customer_city', 'total_orders'], ascending=[True, False])
        top_category_per_city = top_category_per_city.loc[top_category_per_city.groupby('customer_city')['total_orders'].idxmax()]
        top_category_per_city = top_category_per_city.sort_values(by='total_orders', ascending=False)

        # Get top 10 cities
        top_10_cities = top_category_per_city['customer_city'].head(10)
        top_10_data = top_category_per_city[top_category_per_city['customer_city'].isin(top_10_cities)]

        # Create figure for categories
        fig2 = go.Figure(data=[
            go.Bar(
                x=top_10_data['customer_city'],
                y=top_10_data['total_orders'],
                text=top_10_data['product_category_name_english'],
                textposition='auto',
                marker_color='lightblue'
            )
        ])
        
        fig2.update_layout(
            title="Most Popular Product Category per City (Top 10)",
            xaxis_title="City",
            yaxis_title="Number of Orders",
            xaxis_tickangle=-45,
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)

    # Add metrics
    st.header("Key Metrics")
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

    with metrics_col1:
        total_orders = len(orders_df[orders_df['order_purchase_timestamp'].dt.year == latest_year])
        st.metric("Total Orders", f"{total_orders:,}")

    with metrics_col2:
        total_cities = len(orders_with_city['customer_city'].unique())
        st.metric("Total Cities", f"{total_cities:,}")

    with metrics_col3:
        avg_orders_per_city = total_orders / total_cities
        st.metric("Average Orders per City", f"{avg_orders_per_city:.1f}")

    # Add data tables
    st.header("Detailed Data")
    
    if st.checkbox("Show Top Cities Data"):
        st.write("Top 10 Cities by Order Count")
        st.dataframe(pd.DataFrame({
            'City': top_cities_last_year.index,
            'Number of Orders': top_cities_last_year.values
        }))

    if st.checkbox("Show Top Categories Data"):
        st.write("Most Popular Categories by City")
        st.dataframe(top_10_data)

except FileNotFoundError as e:
    st.error("""
        Error: Unable to load data files. Please check the following:
        1. Make sure you are running the script from the 'dashboard' directory
        2. Verify that all data files exist in the '../data' directory:
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