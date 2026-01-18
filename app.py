import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Tokopedia Reviews Insight Dashboard",
    page_icon="📊",
    layout="wide",
)

# ---------- Helpers ----------
OUTPUT_DIR = Path("outputs")

DEFAULT_FILES = {
    "Word Count": OUTPUT_DIR / "wordcount.csv",
    "Positive Words": OUTPUT_DIR / "positive_words.csv",
    "Negative Words": OUTPUT_DIR / "negative_words.csv",
    "Category Count": OUTPUT_DIR / "category_count.csv",
    "Avg Rating Category": OUTPUT_DIR / "avg_rating_category.csv",
    "Problem Products": OUTPUT_DIR / "problem_products.csv",
}

@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def insight_box(title: str, points: list[str], kind: str = "info"):
    """
    kind: 'info' | 'success' | 'warning' | 'error'
    """
    text = "\n".join([f"- {p}" for p in points])
    if kind == "success":
        st.success(f"**{title}**\n\n{text}")
    elif kind == "warning":
        st.warning(f"**{title}**\n\n{text}")
    elif kind == "error":
        st.error(f"**{title}**\n\n{text}")
    else:
        st.info(f"**{title}**\n\n{text}")

def quick_takeaways(df_word, df_cat, df_avg, df_prob):
    bullets = []
    if df_word is not None and not df_word.empty:
        bullets.append(
            f"Kata paling dominan: **{df_word.iloc[0]['word']}** "
            f"(muncul **{int(df_word.iloc[0]['count']):,}x**) → indikator tema utama ulasan."
        )
    if df_cat is not None and not df_cat.empty:
        bullets.append(
            f"Kategori paling ramai: **{df_cat.iloc[0]['category']}** "
            f"(**{int(df_cat.iloc[0]['review_count']):,}** ulasan) → peluang pasar terbesar."
        )
    if df_avg is not None and not df_avg.empty and "avg_rating" in df_avg.columns:
        best = df_avg.sort_values("avg_rating", ascending=False).iloc[0]
        bullets.append(
            f"Kualitas terbaik: **{best['category']}** (avg **{best['avg_rating']:.2f}**) "
            f"→ jadikan referensi standar layanan."
        )
    if df_prob is not None and not df_prob.empty:
        bullets.append(
            f"Produk paling sering dikeluhkan: **{df_prob.iloc[0]['product_name']}** "
            f"(**{int(df_prob.iloc[0]['negative_review_count']):,}** keluhan rating rendah) "
            f"→ prioritas investigasi."
        )
    return bullets

def show_kpis(df_word=None, df_cat=None, df_avg=None):
    c1, c2 = st.columns(2)

    if df_cat is not None and len(df_cat) > 0:
        top_cat = df_cat.iloc[0, 0]
        top_cat_count = int(df_cat.iloc[0, 1])
        c1.metric("Most Reviewed Category", str(top_cat))
        c2.metric("Reviews (Top Category)", f"{top_cat_count:,}")
    else:
        c1.metric("Most Reviewed Category", "-")
        c2.metric("Reviews (Top Category)", "-")

    if df_avg is not None and len(df_avg) > 0 and "avg_rating" in df_avg.columns:
        best = df_avg.sort_values("avg_rating", ascending=False).iloc[0]
        st.info(
            f"⭐ Best avg rating category: **{best['category']}** "
            f"(avg **{best['avg_rating']:.2f}**, reviews **{int(best['review_count']):,}**)"
        )

def bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str, topn: int = 20, color_scheme="blues"):
    if df is None or df.empty:
        st.warning("Data is empty / not loaded.")
        return
    d = df.copy().head(topn)
    st.subheader(title)
    
    # Create Plotly horizontal bar chart for better readability
    fig = px.bar(d, x=y_col, y=x_col, orientation='h',
                 labels={x_col: x_col.replace('_', ' ').title(), y_col: y_col.replace('_', ' ').title()},
                 color=y_col, color_continuous_scale=color_scheme,
                 text=y_col)
    
    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig.update_layout(
        height=max(400, topn * 20),
        yaxis={'categoryorder':'total ascending'},
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

def dataframe_with_download(df: pd.DataFrame, filename: str):
    st.dataframe(df, use_container_width=True, height=420)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
    )

def resolve_file(label: str, default_path: Path):
    st.markdown(f"**{label}**")
    use_upload = st.checkbox(f"Upload file for {label}", key=f"up_{label}", value=False)

    if use_upload:
        up = st.file_uploader(f"Upload {label} CSV", type=["csv"], key=f"uploader_{label}")
        if up is not None:
            return up
        return None
    else:
        path_str = st.text_input(
            f"Local path for {label}",
            value=str(default_path),
            key=f"path_{label}",
        )
        return path_str

def safe_load(source):
    if source is None:
        return None, "No source selected."
    try:
        if hasattr(source, "read"):  # uploaded file
            df = pd.read_csv(source)
        else:
            p = Path(str(source))
            if not p.exists():
                return None, f"File not found: {p}"
            df = load_csv(str(p))
        return df, None
    except Exception as e:
        return None, str(e)

def normalize_two_cols(df: pd.DataFrame, cols=("key", "value")):
    # For outputs like: word,count OR category,review_count OR product_name,negative_review_count
    if df is None or df.empty:
        return df
    if len(df.columns) >= 2:
        df = df.rename(columns={df.columns[0]: cols[0], df.columns[1]: cols[1]})
    return df

# ---------- Sidebar ----------
# Custom CSS for button-style menu
st.markdown("""
<style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    }
    
    /* Button menu styling */
    .menu-button {
        display: block;
        width: 100%;
        padding: 12px 16px;
        margin: 8px 0;
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        color: white;
        text-align: left;
        font-size: 15px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
    }
    
    .menu-button:hover {
        background: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.4);
        transform: translateX(5px);
    }
    
    .menu-button.active {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        border-color: #00d2ff;
        box-shadow: 0 4px 15px rgba(0, 210, 255, 0.4);
    }
    
    /* Sidebar title */
    [data-testid="stSidebar"] h1 {
        color: white;
        font-size: 24px;
        margin-bottom: 20px;
    }
    
    /* Slider styling */
    [data-testid="stSidebar"] .stSlider > div > div {
        color: white;
    }
    
    /* Caption styling */
    [data-testid="stSidebar"] .stCaption {
        color: rgba(255, 255, 255, 0.7);
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("📌 Insight Menu")

# Initialize session state for menu
if "menu" not in st.session_state:
    st.session_state.menu = "Overview"

# Menu options
menu_options = [
    ("🏠", "Overview"),
    ("💬", "Word Insights"),
    ("😊😠", "Positive vs Negative"),
    ("📊", "Category Performance"),
    ("⚠️", "Problem Products"),
    ("⚙️", "Settings / Data Loader"),
]

# Create button-style menu
st.sidebar.markdown('<div style="margin-top: 10px;">', unsafe_allow_html=True)
for icon, label in menu_options:
    if st.sidebar.button(f"{icon} {label}", key=f"btn_{label}", use_container_width=True):
        st.session_state.menu = label

menu = st.session_state.menu
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
topn = st.sidebar.slider("Top-N to Display", min_value=10, max_value=100, value=30, step=5)

# ---------- Data Loader (paths / uploads) ----------
st.title("Tokopedia Reviews Insight Dashboard")

with st.expander("📂 Data Sources (click to configure)", expanded=(menu == "Settings / Data Loader")):
    src_word = resolve_file("Word Count", DEFAULT_FILES["Word Count"])
    src_pos  = resolve_file("Positive Words", DEFAULT_FILES["Positive Words"])
    src_neg  = resolve_file("Negative Words", DEFAULT_FILES["Negative Words"])
    src_cat  = resolve_file("Category Count", DEFAULT_FILES["Category Count"])
    src_avg  = resolve_file("Avg Rating Category", DEFAULT_FILES["Avg Rating Category"])
    src_prob = resolve_file("Problem Products", DEFAULT_FILES["Problem Products"])

# Load data
df_word, err_word = safe_load(src_word)
df_pos,  err_pos  = safe_load(src_pos)
df_neg,  err_neg  = safe_load(src_neg)
df_cat,  err_cat  = safe_load(src_cat)
df_avg,  err_avg  = safe_load(src_avg)
df_prob, err_prob = safe_load(src_prob)

# ---------- Validate / Normalize Columns ----------
df_word = normalize_two_cols(df_word, ("word", "count"))
df_pos  = normalize_two_cols(df_pos,  ("word", "count"))
df_neg  = normalize_two_cols(df_neg,  ("word", "count"))
df_cat  = normalize_two_cols(df_cat,  ("category", "review_count"))
df_prob = normalize_two_cols(df_prob, ("product_name", "negative_review_count"))

# avg rating expected columns: category,avg_rating,review_count
if df_avg is not None and not df_avg.empty:
    col_map = {}
    if "category" not in df_avg.columns and len(df_avg.columns) >= 1:
        col_map[df_avg.columns[0]] = "category"
    if "avg_rating" not in df_avg.columns and len(df_avg.columns) >= 2:
        col_map[df_avg.columns[1]] = "avg_rating"
    if "review_count" not in df_avg.columns and len(df_avg.columns) >= 3:
        col_map[df_avg.columns[2]] = "review_count"
    df_avg = df_avg.rename(columns=col_map)

    for c in ["avg_rating", "review_count"]:
        if c in df_avg.columns:
            df_avg[c] = pd.to_numeric(df_avg[c], errors="coerce")

# ---------- Show errors (non-blocking) ----------
errs = [
    ("Word Count", err_word),
    ("Positive", err_pos),
    ("Negative", err_neg),
    ("Category Count", err_cat),
    ("Avg Rating", err_avg),
    ("Problem Products", err_prob),
]
with st.expander("⚠️ Data Load Status", expanded=False):
    for name, e in errs:
        if e:
            st.error(f"{name}: {e}")
        else:
            st.success(f"{name}: loaded")

# ---------- Pages ----------
if menu == "Overview":
    st.subheader("Overview")
    show_kpis(df_word, df_cat, df_avg)

    bullets = quick_takeaways(df_word, df_cat, df_avg, df_prob)
    if bullets:
        st.success("\n".join([f"• {b}" for b in bullets]))
    else:
        st.info("Load data terlebih dahulu untuk melihat insight.")

    colA, colB = st.columns(2)
    with colA:
        if df_cat is not None and not df_cat.empty:
            bar_chart(df_cat, "category", "review_count", f"📦 Top {topn} Categories by Review Volume", topn=topn, color_scheme="blues")
            st.caption("💡 Kategori dengan ulasan tertinggi = demand tinggi → prioritas stok & marketing")
        else:
            st.warning("Category count not loaded.")

    with colB:
        if df_avg is not None and not df_avg.empty and {"category", "avg_rating"}.issubset(df_avg.columns):
            d = df_avg.sort_values("avg_rating", ascending=False).head(topn)
            st.subheader(f"⭐ Top {topn} Categories by Avg Rating")
            
            fig = px.bar(d, x="avg_rating", y="category", orientation='h',
                         labels={"category": "Category", "avg_rating": "Average Rating"},
                         color="avg_rating", color_continuous_scale="RdYlGn",
                         text="avg_rating", range_x=[0, 5])
            
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig.update_layout(
                height=max(400, topn * 20),
                yaxis={'categoryorder':'total ascending'},
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("💡 Rating tinggi = kualitas stabil. Rating rendah = perlu audit QC & seller")
        else:
            st.warning("Avg rating per category not loaded / columns mismatch.")

    st.markdown("---")
    st.subheader("🎯 Strategic Recommendations")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("**High Volume + High Rating**\n\nPrioritas promosi")
    with col2:
        st.warning("**High Volume + Low Rating**\n\nPrioritas perbaikan")
    with col3:
        st.info("**Low Volume + High Rating**\n\nNiche potensial")

elif menu == "Word Insights":
    st.subheader("💬 Word Insights")

    if df_word is None or df_word.empty:
        st.warning("Word count data not loaded.")
    else:
        bar_chart(df_word, "word", "count", f"Top {topn} Words in Reviews", topn=topn, color_scheme="purples")

        top_words = df_word.head(10)["word"].astype(str).tolist()
        st.info(f"**Top 10:** {', '.join(top_words)}")
        st.caption("💡 Kata dominan menunjukkan tema utama review & driver kepuasan pelanggan")

        st.markdown("### 📊 Detail Data")
        dataframe_with_download(df_word.head(topn), "top_words.csv")

elif menu == "Positive vs Negative":
    st.subheader("😊 Positive vs 😠 Negative Words")
    st.caption("💡 Driver kepuasan vs akar keluhan untuk aksi perbaikan yang tepat")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 😊 Positive (rating ≥ 4)")
        if df_pos is None or df_pos.empty:
            st.warning("Positive words data not loaded.")
        else:
            bar_chart(df_pos, "word", "count", f"Top {topn} Positive Words", topn=topn, color_scheme="greens")
            st.caption("✅ Jadikan selling points untuk marketing & copywriting")
            dataframe_with_download(df_pos.head(topn), "positive_words_top.csv")

    with c2:
        st.markdown("### 😠 Negative (rating ≤ 2)")
        if df_neg is None or df_neg.empty:
            st.warning("Negative words data not loaded.")
        else:
            bar_chart(df_neg, "word", "count", f"Top {topn} Negative Words", topn=topn, color_scheme="reds")
            st.caption("⚠️ Root cause keluhan → perkuat QC & validasi seller")
            dataframe_with_download(df_neg.head(topn), "negative_words_top.csv")



elif menu == "Category Performance":
    st.subheader("📊 Category Performance")
    st.caption("💡 Potensi pasar (volume) vs kualitas pengalaman (rating) per kategori")

    left, right = st.columns(2)

    with left:
        st.markdown("### 📦 Review Volume per Category")
        if df_cat is None or df_cat.empty:
            st.warning("Category count not loaded.")
        else:
            bar_chart(df_cat, "category", "review_count", f"Top {topn} Categories", topn=topn, color_scheme="blues")
            st.caption("✅ Prioritas marketing & stok")
            dataframe_with_download(df_cat.head(topn), "category_review_count_top.csv")

    with right:
        st.markdown("### ⭐ Avg Rating per Category")
        if df_avg is None or df_avg.empty or not {"category", "avg_rating", "review_count"}.issubset(df_avg.columns):
            st.warning("Avg rating per category not loaded / columns mismatch.")
        else:
            d = df_avg.sort_values("avg_rating", ascending=False).head(topn)
            
            fig = px.bar(d, x="avg_rating", y="category", orientation='h',
                         labels={"category": "Category", "avg_rating": "Average Rating"},
                         color="avg_rating", color_continuous_scale="RdYlGn",
                         text="avg_rating", range_x=[0, 5])
            
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig.update_layout(
                height=max(400, topn * 20),
                yaxis={'categoryorder':'total ascending'},
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("⚠️ Rating rendah perlu audit QC & seller")
            dataframe_with_download(d, "category_avg_rating_top.csv")

    st.markdown("---")
    st.subheader("🎯 Category Opportunity Matrix")

    if (df_cat is not None and not df_cat.empty) and (df_avg is not None and not df_avg.empty):
        m = pd.merge(df_cat, df_avg, on="category", how="inner", suffixes=("", "_avg"))

        # Handle review_count column - use the one from df_cat if duplicated
        if "review_count_avg" in m.columns and "review_count" not in m.columns:
            m = m.rename(columns={"review_count_avg": "review_count"})
        elif "review_count_avg" in m.columns:
            m = m.drop(columns=["review_count_avg"])

        # normalize numeric
        if "review_count" in m.columns:
            m["review_count"] = pd.to_numeric(m["review_count"], errors="coerce")
        if "avg_rating" in m.columns:
            m["avg_rating"] = pd.to_numeric(m["avg_rating"], errors="coerce")

        # Create scatter plot for opportunity matrix
        fig = px.scatter(m, x="review_count", y="avg_rating", 
                        hover_data=["category"],
                        size="review_count",
                        color="avg_rating",
                        color_continuous_scale="RdYlGn",
                        labels={"review_count": "Review Volume", "avg_rating": "Avg Rating"},
                        range_y=[0, 5])
        
        fig.update_layout(height=500, showlegend=False)
        fig.add_hline(y=3.5, line_dash="dash", line_color="gray", annotation_text="Quality Threshold")
        fig.add_vline(x=m["review_count"].median(), line_dash="dash", line_color="gray", annotation_text="Volume Median")
        
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.success("**High Vol + High Rating**\n\nPromosi")
        with col2:
            st.warning("**High Vol + Low Rating**\n\nPerbaikan")
        with col3:
            st.info("**Low Vol + High Rating**\n\nNiche")
        with col4:
            st.error("**Low Vol + Low Rating**\n\nEvaluasi")

        st.markdown("### 📋 Detail Matrix")
        st.dataframe(
            m.sort_values(["review_count", "avg_rating"], ascending=[False, False]).head(50),
            use_container_width=True,
            height=420,
        )
    else:
        st.info("Load Category Count & Avg Rating first.")

elif menu == "Problem Products":
    st.subheader("⚠️ Problem Products")
    st.caption("💡 Early warning: produk dengan rating rendah terbanyak → risiko retur & reputasi")

    if df_prob is None or df_prob.empty:
        st.warning("Problem products data not loaded.")
    else:
        bar_chart(df_prob, "product_name", "negative_review_count", f"Top {topn} Problem Products", topn=topn, color_scheme="reds")

        top_prod = df_prob.head(5)["product_name"].astype(str).tolist()
        st.error(f"🚨 **Prioritas investigasi:** {', '.join(top_prod)}")
        st.caption("✅ Cek: deskripsi, QC, packaging, SLA pengiriman")

        st.markdown("### 📋 Detail Data")
        dataframe_with_download(df_prob.head(topn), "problem_products_top.csv")

else:
    st.subheader("⚙️ Settings / Data Loader")
    st.info("Atur file path atau upload CSV melalui panel **Data Sources** di atas. Pastikan format CSV dengan header.")
