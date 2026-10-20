import pandas as pd
import plotly.express as px
import streamlit as st

URL = "https://raw.githubusercontent.com/intro-stat-learning/ISLP/main/ISLP/data/College.csv"

st.set_page_config(page_title="Graduation rates of US colleges", layout="wide")
st.title("Do private colleges graduate more students, and what do they cost?")
st.caption("Reader: a family choosing where to apply. Decision: which kind of college to shortlist. "
           "Data: ISLP College (US colleges, 1995). One impossible graduation rate of 118% is removed.")

# Step 1. Load and clean the data once; the result is cached between reruns
@st.cache_data
def load():
    d = pd.read_csv(URL)
    if "Unnamed: 0" in d.columns:
        d = d.rename(columns={"Unnamed: 0": "College"})
    if "College" not in d.columns:
        d.insert(0, "College", [f"College {i + 1}" for i in range(len(d))])
    d = d[d["Grad.Rate"] <= 100].copy()
    d["Type"] = d["Private"].map({"Yes": "Private", "No": "Public"})
    return d

college = load()

# Step 2. Filters in the sidebar
st.sidebar.header("Filters")
types = st.sidebar.multiselect("Type of college", ["Private", "Public"], default=["Private", "Public"])
t_min, t_max = int(college["Outstate"].min()), int(college["Outstate"].max())
tuition = st.sidebar.slider("Out-of-state tuition ($)", t_min, t_max, (t_min, t_max), step=100)
r_min, r_max = float(college["S.F.Ratio"].min()), float(college["S.F.Ratio"].max())
ratio = st.sidebar.slider("Students per faculty member", r_min, r_max, (r_min, r_max), step=0.5)

# Step 3. Filter the data; every chart below uses d, so all charts are linked
d = college[college["Type"].isin(types)
            & college["Outstate"].between(*tuition)
            & college["S.F.Ratio"].between(*ratio)]
if d.empty:
    st.warning("No colleges match these filters. Choose more options in the sidebar.")
    st.stop()

colors = {"Private": "#0072B2", "Public": "#E69F00"}   # colour-blind safe, same on every chart

# Step 4a. KPI cards
k1, k2, k3, k4 = st.columns(4)
k1.metric("Colleges selected", len(d))
k2.metric("Average graduation rate", f"{d['Grad.Rate'].mean():.1f}%")
k3.metric("Average out-of-state tuition", f"${d['Outstate'].mean():,.0f}")
k4.metric("Average spending per student", f"${d['Expend'].mean():,.0f}")

# Step 4b. Four linked charts in a 2 x 2 grid
c1, c2 = st.columns(2)
c1.plotly_chart(px.scatter(d, x="Outstate", y="Grad.Rate", color="Type", hover_name="College",
                           color_discrete_map=colors,
                           title="Higher tuition goes with higher graduation rates",
                           labels={"Outstate": "Out-of-state tuition ($)", "Grad.Rate": "Graduation rate (%)"}),
                width="stretch")
c2.plotly_chart(px.histogram(d, x="Grad.Rate", color="Type", nbins=20, barmode="overlay", opacity=0.7,
                             color_discrete_map=colors,
                             title="Private colleges cluster at higher graduation rates",
                             labels={"Grad.Rate": "Graduation rate (%)", "count": "Number of colleges"}),
                width="stretch")
c3, c4 = st.columns(2)
c3.plotly_chart(px.box(d, x="Type", y="Expend", color="Type", color_discrete_map=colors,
                       title="Private colleges spend more per student",
                       labels={"Expend": "Spending per student ($)", "Type": ""}),
                width="stretch")
bands = pd.cut(d["S.F.Ratio"], [0, 10, 12, 14, 16, 18, 20, 40]).astype(str)
by_ratio = d.groupby(bands, as_index=False)["Grad.Rate"].mean()
by_ratio.columns = ["ratio", "grad"]
fig4 = px.bar(by_ratio, x="ratio", y="grad", title="Crowded classrooms, lower graduation rates",
              labels={"ratio": "Students per faculty member", "grad": "Average graduation rate (%)"})
fig4.update_yaxes(range=[0, 100])   # bars start at zero
c4.plotly_chart(fig4, width="stretch")

# Step 4c. The data behind the charts, and a download button
with st.expander("Show the data"):
    st.dataframe(d.sort_values("Grad.Rate", ascending=False), width="stretch")
    st.download_button("Download as CSV", d.to_csv(index=False), "college_filtered.csv")
