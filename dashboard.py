# -- coding: utf-8 --
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import arabic_reshaper
from bidi.algorithm import get_display
from matplotlib.ticker import FuncFormatter
import squarify
import seaborn as sns  

# ================================
# الإعدادات
# ================================
st.set_page_config(page_title="📊 Retail Data Analysis Project", layout="wide")

# 🎨 تغيير لون الخلفية
page_bg = """
<style>
.stApp {
    background-color: #e6f2ff; /* 👈 لون الخلفية */
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

st.title("📊 Retail Data Analysis Project - إعداد: Ezz Afify ✨")

# الاتصال بقاعدة البيانات
client = MongoClient("mongodb://localhost:27017/")
db = client["STUDENTGUIDE"]

# دالة لضبط النص العربي
def fix_arabic(text):
    try:
        return get_display(arabic_reshaper.reshape(str(text)))
    except:
        return str(text)

# ================================
# القائمة الجانبية
# ================================
st.sidebar.markdown("## 👨‍💻 المطور")
st.sidebar.success("*Ezz Afify*")

menu = st.sidebar.selectbox(
    "📊 Choose Analysis:",
    [
        "👤 Top 10 Customers",
        "📦 Top 10 Products",
        "🏬 Best-Selling Products by Branch",
        "💰 Top 20 Branches by Revenue",
        "📈 Monthly Sales Analysis",
        "🌦 Seasonal Sales Analysis",
        "🏆 Best Product in Each Season",
        "📊 Most Demanded Products",
    ]
)


# ================================
# 👤 أعلى 10 عملاء
# ================================
if menu == "👤 Top 10 Customers":
    cursor = db["Collection"].find({}, {"CustomerID": 1, "CustomerName": 1, "TotalPrice": 1, "_id": 0})
    df_customers = pd.DataFrame(list(cursor))

    if not df_customers.empty:
        top_customers = (
            df_customers.groupby(["CustomerID", "CustomerName"])["TotalPrice"]
            .sum().sort_values(ascending=False).head(10).reset_index()
        )

        customer_names = [fix_arabic(name) for name in top_customers["CustomerName"]]
        total_spent = top_customers["TotalPrice"]

        # Pie Chart
        fig, ax = plt.subplots(figsize=(9, 9))

        wedges, texts, autotexts = ax.pie(
            total_spent,
            autopct=lambda pct: f"{pct:.1f}%\n{int(pct/100.*sum(total_spent)):,.0f}",
            textprops=dict(color="white", fontsize=10),
            startangle=140
        )

        # أسماء العملاء مرقمة (1، 2، 3 ...)
        customer_labels = [f"{i+1}. {name}" for i, name in enumerate(customer_names)]

        # Legend مرتب
        ax.legend(
            wedges, customer_labels,
            title="Top Customers",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )

        ax.set_title("Top Customers (Spending Share)", fontsize=18)

        plt.tight_layout()
        st.pyplot(fig)


# ================================
# 📦 أعلى 10 منتجات
# ================================
elif menu == "📦 Top 10 Products":
    cursor = db["Collection"].find({}, {"ProductID": 1, "ProductName": 1, "Quantity": 1, "_id": 0})
    df_products = pd.DataFrame(list(cursor))

    if not df_products.empty:
        top_products = (
            df_products.groupby(["ProductID", "ProductName"])["Quantity"]
            .sum().sort_values(ascending=False).head(10).reset_index()
        )

        product_names = [fix_arabic(name) for name in top_products["ProductName"]]
        quantities = top_products["Quantity"]

        fig2, ax2 = plt.subplots(figsize=(12, 6))
        bars = ax2.barh(product_names, quantities, color="blue")
        ax2.set_xlabel("Quantity Sold", fontsize=12)
        ax2.set_ylabel("Product Name", fontsize=12)
        ax2.set_title("Best-Selling Products (Overall)", fontsize=20)

        ax2.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))

        for bar, value in zip(bars, quantities):
            ax2.text(bar.get_width() + (bar.get_width() * 0.01),
                     bar.get_y() + bar.get_height() / 2,
                     f"{value:,.0f}", va="center", fontsize=10)

        st.pyplot(fig2)

# ================================
# 🏬 أفضل المنتجات حسب الفروع (Treemap)
# ================================
elif menu == "🏬 Best-Selling Products by Branch":
    cursor = db["Collection"].find({}, {"BranchID": 1, "BranchName": 1, "ProductName": 1, "Quantity": 1, "_id": 0})
    df_branch_products = pd.DataFrame(list(cursor))

    if not df_branch_products.empty:
        top_branch_products = (
            df_branch_products.groupby(["BranchID", "BranchName", "ProductName"])["Quantity"]
            .sum().sort_values(ascending=False).head(20).reset_index()
        )

        branch_names = [fix_arabic(name) for name in top_branch_products["BranchName"]]
        product_names = [fix_arabic(name) for name in top_branch_products["ProductName"]]
        quantities = top_branch_products["Quantity"]

        labels = [f"{b}\n{p}\n{q:,.0f}" for b, p, q in zip(branch_names, product_names, quantities)]

        fig3 = plt.figure(figsize=(20, 10))
        squarify.plot(sizes=quantities, label=labels, alpha=0.9, text_kwargs={"fontsize": 12})
        plt.title("Best-Selling Products by Branch", fontsize=18)
        plt.axis("off")

        st.pyplot(fig3)

# ================================
# 💰 أعلى 20 فرع حسب الإيرادات (Treemap)
# ================================
elif menu == "💰 Top 20 Branches by Revenue":
    cursor = db["Collection"].find({}, {"BranchID": 1, "BranchName": 1, "Quantity": 1, "Price": 1, "_id": 0})
    df_branch = pd.DataFrame(list(cursor))

    if not df_branch.empty:
        df_branch["Revenue"] = df_branch["Quantity"] * df_branch["Price"]

        branch_comparisons = (
            df_branch.groupby(["BranchID", "BranchName"])["Revenue"]
            .sum().reset_index().rename(columns={"Revenue": "Total Revenue"})
            .sort_values("Total Revenue", ascending=False)
        )

        top20_branches = branch_comparisons.head(20).reset_index(drop=True)

        labels = [f"{i+1}. {fix_arabic(branch)}\n{rev:,.0f}"
                  for i, (branch, rev) in enumerate(zip(top20_branches["BranchName"], top20_branches["Total Revenue"]))]

        sizes = top20_branches["Total Revenue"]

        fig4 = plt.figure(figsize=(20, 10))
        squarify.plot(sizes=sizes, label=labels, alpha=0.9, text_kwargs={"fontsize": 10})
        plt.title("Top 20 Branches by Revenue", fontsize=18)
        plt.axis("off")

        st.pyplot(fig4)

# ================================
# 📈 تحليل المبيعات شهريًا
# ================================
elif menu == "📈 Monthly Sales Analysis":
    cursor = db["Collection"].find({}, {"SaleDate": 1, "TotalPrice": 1, "_id": 0})
    df_sales = pd.DataFrame(list(cursor))

    if not df_sales.empty:
        df_sales["SaleDate"] = pd.to_datetime(df_sales["SaleDate"])

        monthly_sales = (
            df_sales.groupby(df_sales["SaleDate"].dt.to_period("M"))["TotalPrice"]
            .sum().reset_index()
        )
        monthly_sales["SaleDate"] = monthly_sales["SaleDate"].dt.to_timestamp()
        monthly_sales = monthly_sales.sort_values("SaleDate")

        fig5, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6), gridspec_kw={'width_ratios': [2, 1]})
        ax1.plot(monthly_sales["SaleDate"], monthly_sales["TotalPrice"], marker="o", linestyle="-", color="blue")

        ax1.set_xlabel("Month", fontsize=12)
        ax1.set_ylabel("Total Price", fontsize=12)
        ax1.set_title("Time Analysis (Monthly Trends)", fontsize=14)

        ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b-%Y"))
        plt.setp(ax1.get_xticklabels(), rotation=45)
        ax1.grid(True)

        table_data = monthly_sales[["SaleDate", "TotalPrice"]].copy()
        table_data["SaleDate"] = table_data["SaleDate"].dt.strftime("%Y-%m")
        table_data["TotalPrice"] = table_data["TotalPrice"].apply(lambda x: f"{int(x):,}")

        ax2.axis("off")
        tbl = ax2.table(cellText=table_data.values, colLabels=table_data.columns,
                        cellLoc="center", loc="center")
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(9)
        tbl.scale(1.2, 1.2)

        plt.tight_layout()
        st.pyplot(fig5)

# ================================
# 🌦 تحليل المبيعات الموسمية
# ================================
elif menu == "🌦 Seasonal Sales Analysis":
    cursor = db["Collection"].find({}, {"SaleDate": 1, "TotalPrice": 1, "_id": 0})
    df_sales = pd.DataFrame(list(cursor))

    if not df_sales.empty:
        df_sales["SaleDate"] = pd.to_datetime(df_sales["SaleDate"])
        df_sales["Month"] = df_sales["SaleDate"].dt.month

        def get_season(month):
            if month in [12, 1, 2]: return "Winter"
            elif month in [3, 4, 5]: return "Spring"
            elif month in [6, 7, 8]: return "Summer"
            else: return "Autumn"

        df_sales["Season"] = df_sales["Month"].apply(get_season)

        seasonal_sales = (
            df_sales.groupby("Season")["TotalPrice"]
            .sum().reset_index().sort_values("TotalPrice", ascending=False)
        )

        fig6, ax = plt.subplots(figsize=(10, 6))
        ax.plot(seasonal_sales["Season"], seasonal_sales["TotalPrice"], marker="o", linestyle="-", color="green")

        ax.set_xlabel("Season", fontsize=12)
        ax.set_ylabel("Total Sales", fontsize=12)
        ax.set_title("Time Analysis (Seasonal Trends)", fontsize=14)

        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

        for i, value in enumerate(seasonal_sales["TotalPrice"]):
            ax.text(seasonal_sales["Season"].iloc[i], value + (value*0.01),
                    f"{int(value):,}", ha="center", fontsize=10, color="red")

        ax.grid(True)
        st.pyplot(fig6)

# ================================
# 🏆 أفضل منتج في كل موسم
# ================================
elif menu == "🏆 Best Product in Each Season":
    cursor = db["Collection"].find({}, {"ProductID": 1, "ProductName": 1, "TotalPrice": 1, "SaleDate": 1, "_id": 0})
    df_products_season = pd.DataFrame(list(cursor))

    if not df_products_season.empty:
        df_products_season["SaleDate"] = pd.to_datetime(df_products_season["SaleDate"])
        df_products_season["Month"] = df_products_season["SaleDate"].dt.month

        def get_season(month):
            if month in [12, 1, 2]: return "Winter"
            elif month in [3, 4, 5]: return "Spring"
            elif month in [6, 7, 8]: return "Summer"
            else: return "Autumn"

        df_products_season["Season"] = df_products_season["Month"].apply(get_season)

        seasonal_products = (
            df_products_season.groupby(["Season", "ProductID", "ProductName"])["TotalPrice"]
            .sum().reset_index()
        )

        seasonal_products["Season"] = pd.Categorical(seasonal_products["Season"],
                                                     categories=["Winter", "Spring", "Summer", "Autumn"],
                                                     ordered=True)

        top_products_per_season = (
            seasonal_products.sort_values(["Season", "TotalPrice"], ascending=[True, False])
            .groupby("Season").head(1).reset_index(drop=True)
        )

        top_products_per_season["ProductName"] = top_products_per_season["ProductName"].apply(fix_arabic)

        fig7, ax7 = plt.subplots(figsize=(10, 6))
        sns.barplot(data=top_products_per_season, x="Season", y="TotalPrice",
                    hue="Season", dodge=False,
                    palette={"Winter":"#5DADE2","Spring":"#58D68D","Summer":"#F7DC6F","Autumn":"#EB984E"}, ax=ax7)

        for i, row in top_products_per_season.iterrows():
            ax7.text(i, row["TotalPrice"] + (row["TotalPrice"]*0.01),
                     f"{row['ProductName']}\n{row['TotalPrice']:,.0f}",
                     ha="center", va="bottom", fontsize=9)

        ax7.set_title("Seasonal Product Demand (Top Product per Season)", fontsize=14)
        ax7.set_xlabel("Season", fontsize=12)
        ax7.set_ylabel("Total Price", fontsize=12)

        st.pyplot(fig7)

# ================================
# 📊 المنتجات الأكثر احتياجًا
# ================================
elif menu == "📊 Most Demanded Products":
    cursor = db["Collection"].find({}, {"BranchID": 1, "BranchName": 1, "ProductID": 1, "ProductName": 1, "Quantity": 1, "_id": 0})
    df_branch_needs = pd.DataFrame(list(cursor))

    if not df_branch_needs.empty:
        product_demand = df_branch_needs.groupby(["ProductID", "ProductName"])["Quantity"].sum().reset_index()
        top_product = product_demand.sort_values("Quantity", ascending=False).head()
        top_product["ProductName_fixed"] = top_product["ProductName"].apply(fix_arabic)

        fig8, ax8 = plt.subplots(figsize=(12, 6))
        ax8.scatter(top_product["ProductName_fixed"], top_product["Quantity"],
                    s=top_product["Quantity"] / 10, edgecolors="k")

        for i, qty in enumerate(top_product["Quantity"]):
            ax8.text(top_product["ProductName_fixed"].iloc[i], qty,
                     f"{qty:,}", ha="center", va="bottom", fontsize=12)

        ax8.set_title("Stock Planning (Branch Needs)", fontsize=14, color="red")
        ax8.set_xlabel("ProductName", fontsize=12, color="red")
        ax8.set_ylabel("Total quantity required", fontsize=12, color="red")
        ax8.grid(True, linestyle="--", alpha=0.6)

        st.pyplot(fig8)

# ================================
# Footer
# ================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; margin-top: 50px; font-size: 16px;">
        🚀 تم التطوير بواسطة <span style="color:green; font-weight:bold;">Ezz Afify</span><br>
        👨‍🏫 بإشراف <span style="color:blue; font-weight:bold;">Eng. Ahmed Fahmy</span><br>
        📊 <span style="font-style: italic;">Retail Data Analysis Project</span>
    </div>
    """,
    unsafe_allow_html=True
)


