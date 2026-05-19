import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sparrow Analytics",
    page_icon="🐦",
    layout="wide"
)

st.title("🐦 Sparrow Analytics")
st.subheader("U.S. Metro Developer Talent & Wage Intelligence")

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    geo     = pd.read_csv("data/geo_talent_intensity.csv")
    lang    = pd.read_csv("data/language_breakdown.csv")
    hourly  = pd.read_csv("data/events_by_hour.csv")
    weekly  = pd.read_csv("data/user_weekly.csv")
    project = pd.read_csv("data/project_activity.csv")
    push    = pd.read_csv("data/push_by_ref.csv")
    return geo, lang, hourly, weekly, project, push

geo, lang, hourly, weekly, project, push = load_data()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📍 Quadrant Chart",
    "📈 Trends Over Time",
    "💻 Language Breakdown",
    "🏢 Project Activity",
    "🔀 Push Activity"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — QUADRANT CHART
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Metro Contribution Intensity vs Developer Wage Cost")
    st.markdown("""
    **How to read this chart:**
    - 🏆 **Top Left** — High output, lower wages = best value cities
    - 💰 **Top Right** — High output but expensive
    - 😴 **Bottom Left** — Low output and cheap
    - ❌ **Bottom Right** — Expensive with low output
    """)

    # clean nulls
    geo_clean = geo.dropna(subset=["commits_per_developer", "wage_premium_pct"])

    fig = px.scatter(
        geo_clean,
        x="wage_premium_pct",
        y="commits_per_developer",
        text="msa_name",
        size="total_employment",
        color="wage_premium_pct",
        color_continuous_scale="RdYlGn_r",
        hover_data={
            "msa_name":              True,
            "wage_premium_pct":      ":.1f",
            "commits_per_developer": ":.6f",
            "total_employment":      ":,",
            "a_mean":                ":,.0f"
        },
        labels={
            "wage_premium_pct":      "Wage Premium over National Mean (%)",
            "commits_per_developer": "Commits per Developer",
            "total_employment":      "Total SW Developers",
            "a_mean":                "Mean Annual Wage ($)"
        },
        title="Open-Source Contribution Intensity vs Developer Wage Cost"
    )

    # Quadrant lines
    fig.add_hline(
        y=geo_clean["commits_per_developer"].median(),
        line_dash="dash",
        line_color="gray",
        annotation_text="Median commits/developer"
    )
    fig.add_vline(
        x=0,
        line_dash="dash",
        line_color="gray",
        annotation_text="National mean wage"
    )

    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total MSAs", len(geo_clean))
    col2.metric("Total Events", f"{geo_clean['total_events'].sum():,}")
    col3.metric("Total Commits", f"{geo_clean['total_commits'].sum():,.0f}")
    col4.metric("National Mean Wage", f"${geo_clean['national_mean_wage'].iloc[0]:,.0f}")

    # Rankings table
    st.subheader("📊 All Metro Rankings")
    display_geo = geo_clean[[
        "msa_name", "total_events", "total_commits",
        "commits_per_developer", "wage_premium_pct",
        "total_employment", "a_mean"
    ]].rename(columns={
        "msa_name":              "Metro Area",
        "total_events":          "Total Events",
        "total_commits":         "Total Commits",
        "commits_per_developer": "Commits/Developer",
        "wage_premium_pct":      "Wage Premium (%)",
        "total_employment":      "SW Developers",
        "a_mean":                "Mean Annual Wage ($)"
    }).sort_values("Commits/Developer", ascending=False)

    st.dataframe(display_geo, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TRENDS OVER TIME
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("GitHub Activity Trends Over Time")

    hourly["event_hour"] = pd.to_datetime(hourly["event_hour"])
    hourly["date"] = hourly["event_hour"].dt.date

    event_types = hourly["event_type"].unique().tolist()
    selected_types = st.multiselect(
        "Filter by event type",
        options=event_types,
        default=event_types[:3] if len(event_types) >= 3 else event_types
    )

    filtered = hourly[hourly["event_type"].isin(selected_types)]
    daily = (filtered
        .groupby(["date", "event_type"])["event_count"]
        .sum()
        .reset_index())

    fig2 = px.line(
        daily,
        x="date",
        y="event_count",
        color="event_type",
        title="Daily GitHub Event Volume by Type",
        labels={
            "date":        "Date",
            "event_count": "Event Count",
            "event_type":  "Event Type"
        }
    )
    fig2.update_layout(height=450)
    st.plotly_chart(fig2, use_container_width=True)

    # Push by ref
    st.subheader("Main Branch vs Other Branch Pushes")
    fig3 = px.bar(
        push,
        x="branch_category",
        y="push_count",
        color="branch_category",
        title="Push Events by Branch Type",
        labels={
            "branch_category": "Branch Type",
            "push_count":      "Push Count"
        },
        color_discrete_map={
            "main_branch":  "#2ecc71",
            "other_branch": "#3498db",
            "unknown":      "#95a5a6"
        }
    )
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — LANGUAGE BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Programming Language Specialization")

    top_orgs = (lang
        .groupby("org_login")["commit_count"]
        .sum()
        .nlargest(20)
        .index.tolist())

    selected_org = st.selectbox(
        "Select organization",
        options=["All"] + top_orgs
    )

    if selected_org == "All":
        lang_data = (lang
            .groupby("detected_language")["commit_count"]
            .sum()
            .reset_index()
            .nlargest(15, "commit_count"))
    else:
        lang_data = (lang[lang["org_login"] == selected_org]
            .groupby("detected_language")["commit_count"]
            .sum()
            .reset_index()
            .nlargest(15, "commit_count"))

    col1, col2 = st.columns(2)

    with col1:
        fig4 = px.pie(
            lang_data,
            values="commit_count",
            names="detected_language",
            title=f"Language Distribution — {selected_org}",
            hole=0.4
        )
        fig4.update_layout(height=450)
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        fig5 = px.bar(
            lang_data.sort_values("commit_count"),
            x="commit_count",
            y="detected_language",
            orientation="h",
            title=f"Commit Count by Language — {selected_org}",
            labels={
                "commit_count":      "Commit Count",
                "detected_language": "Language"
            },
            color="commit_count",
            color_continuous_scale="Blues"
        )
        fig5.update_layout(height=450)
        st.plotly_chart(fig5, use_container_width=True)

    # Language heatmap
    st.subheader("Language Heatmap — Top Orgs")
    top15_orgs = (lang
        .groupby("org_login")["commit_count"]
        .sum()
        .nlargest(15)
        .index.tolist())

    pivot = (lang[lang["org_login"].isin(top15_orgs)]
        .groupby(["org_login", "detected_language"])["commit_count"]
        .sum()
        .reset_index()
        .pivot(index="org_login", columns="detected_language", values="commit_count")
        .fillna(0))

    fig6 = px.imshow(
        pivot,
        title="Commit Volume Heatmap by Org and Language",
        color_continuous_scale="Blues",
        aspect="auto"
    )
    fig6.update_layout(height=500)
    st.plotly_chart(fig6, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PROJECT ACTIVITY
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("Most Active Repositories")

    top_n = st.slider("Number of repos to show", 5, 50, 15)

    top_projects = (project
        .nlargest(top_n, "total_events")
        [[
            "repo_name", "org_login", "total_events",
            "unique_contributors", "push_count",
            "pr_count", "fork_count", "repo_health_score"
        ]]
        .rename(columns={
            "repo_name":          "Repository",
            "org_login":          "Organization",
            "total_events":       "Total Events",
            "unique_contributors":"Contributors",
            "push_count":         "Pushes",
            "pr_count":           "Pull Requests",
            "fork_count":         "Forks",
            "repo_health_score":  "Health Score"
        }))

    fig7 = px.bar(
        top_projects,
        x="Total Events",
        y="Repository",
        orientation="h",
        color="Health Score",
        color_continuous_scale="Viridis",
        title=f"Top {top_n} Most Active Repositories",
        hover_data=["Organization", "Contributors", "Pushes"]
    )
    fig7.update_layout(height=600, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig7, use_container_width=True)

    st.subheader("Repository Details")
    st.dataframe(top_projects, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — PUSH ACTIVITY
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.header("Push Event Activity")

    col1, col2 = st.columns(2)

    with col1:
        fig8 = px.pie(
            push,
            values="push_count",
            names="branch_category",
            title="Push Events by Branch Category",
            hole=0.4,
            color_discrete_map={
                "main_branch":  "#2ecc71",
                "other_branch": "#3498db",
                "unknown":      "#95a5a6"
            }
        )
        st.plotly_chart(fig8, use_container_width=True)

    with col2:
        fig9 = px.bar(
            push,
            x="branch_category",
            y="total_commits",
            color="branch_category",
            title="Total Commits by Branch Type",
            labels={
                "branch_category": "Branch Type",
                "total_commits":   "Total Commits"
            },
            color_discrete_map={
                "main_branch":  "#2ecc71",
                "other_branch": "#3498db",
                "unknown":      "#95a5a6"
            }
        )
        st.plotly_chart(fig9, use_container_width=True)

    st.subheader("Push Summary")
    st.dataframe(push, use_container_width=True)