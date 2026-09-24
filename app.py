import streamlit as st
import pandas as pd
import plotly.express as px
from pytrends.request import TrendReq

st.set_page_config(page_title="Google Trends Analysis", layout="wide")
st.title("📊 Google Search Trends Analysis")

keyword = st.text_input("Enter keyword", "Cloud Computing")
timeframe = st.selectbox(
    "Select time period",
    ["today 1-m", "today 3-m", "today 12-m", "today 5-y"],
    index=2
)
geo = st.text_input("Country code (leave blank for worldwide)", "")

@st.cache_data(ttl=600, show_spinner=False)
def get_trends_data(keyword, timeframe, geo):
    trends = TrendReq(hl="en-US", tz=360, timeout=(10, 30))
    trends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
    region_df = trends.interest_by_region()
    time_df = trends.interest_over_time()
    return region_df, time_df

related_text = st.text_input(
    "Related keywords (comma separated)",
    "cloud computing, data science, machine learning, artificial intelligence"
)
related_keywords = [
    item.strip() for item in related_text.split(",") if item.strip()
][:5]

if st.button("Analyze"):
    if not keyword.strip():
        st.warning("Please enter a keyword.")
        st.stop()

    try:
        with st.spinner("Fetching Google Trends data..."):
            region_df, time_df = get_trends_data(keyword.strip(), timeframe, geo.strip())

        if region_df.empty or time_df.empty:
            st.warning("No data returned. Try another keyword or time period.")
            st.stop()

        st.subheader(f"Results for: {keyword}")

        # 1. Top 15 countries
        st.markdown("### 1. Top 15 countries")
        country_col = keyword.strip()
        top15 = (
            region_df.sort_values(by=country_col, ascending=False)
            .head(15)
            .reset_index()
        )

        if "geoName" not in top15.columns:
            top15 = top15.rename(columns={top15.columns[0]: "geoName"})

        fig_bar = px.bar(
            top15.sort_values(country_col),
            x=country_col,
            y="geoName",
            orientation="h",
            title=f"Top 15 countries searching for '{keyword}'",
            labels={country_col: "Interest", "geoName": "Country"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # 2. World map
        st.markdown("### 2. World map")
        map_df = region_df.reset_index()
        if "geoName" not in map_df.columns:
            map_df = map_df.rename(columns={map_df.columns[0]: "geoName"})

        fig_map = px.choropleth(
            map_df,
            locations="geoName",
            locationmode="country names",
            color=country_col,
            color_continuous_scale="Blues",
            title=f"Search interest by country: '{keyword}'"
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # 3. Time-wise interest
        st.markdown("### 3. Interest over time")
        value_col = next(
            (col for col in time_df.columns if col != "isPartial"),
            None
        )

        if value_col is None:
            st.warning("Keyword data was not returned.")
        else:
            fig_time = px.line(
                time_df,
                x=time_df.index,
                y=value_col,
                markers=True,
                title=f"Search interest over time: '{value_col}'",
                labels={"x": "Date", value_col: "Interest"}
            )
            st.plotly_chart(fig_time, use_container_width=True)

        # 4. Related keyword comparison
        st.markdown("### 4. Compare related keywords")
        if len(related_keywords) < 2:
            st.warning("Enter at least two related keywords.")
        else:
            compare_trends = TrendReq(
                hl="en-US", tz=360, timeout=(10, 30)
            )
            compare_trends.build_payload(
                related_keywords,
                cat=0,
                timeframe=timeframe,
                geo=geo.strip()
            )
            compare_df = compare_trends.interest_over_time()

            if compare_df.empty:
                st.warning("No comparison data returned.")
            else:
                compare_df = compare_df.drop(
                    columns=["isPartial"], errors="ignore"
                )
                st.line_chart(compare_df)

    except Exception as error:
        st.error(
            "Google Trends request failed. Try again later or use a shorter "
            "time period."
        )
        st.caption(f"Error details: {error}")
else:
    st.info("Enter a keyword and click Analyze.")
