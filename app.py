import time
import pandas as pd
import streamlit as st

from src.matching import compare_label_fields

st.set_page_config(
    page_title="TTB LabelCheck AI",
    page_icon="✅",
    layout="wide"
)

st.title("TTB LabelCheck AI")
st.caption("Human-in-the-loop alcohol label verification assistant")

st.markdown("""
This prototype helps compliance agents compare submitted application fields against label text.
It is designed to assist review, not replace final agent judgment.
""")

with st.sidebar:
    st.header("Application Fields")
    brand_name = st.text_input("Brand Name", "OLD TOM DISTILLERY")
    class_type = st.text_input("Class / Type", "Kentucky Straight Bourbon Whiskey")
    alcohol_content = st.text_input("Alcohol Content", "45% Alc./Vol.")
    net_contents = st.text_input("Net Contents", "750 mL")
    producer_address = st.text_input("Producer / Bottler Address", "Old Tom Distillery, Louisville, KY")
    country_of_origin = st.text_input("Country of Origin", "USA")
    government_warning = st.text_area(
        "Government Warning",
        "GOVERNMENT WARNING: According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."
    )

expected_fields = {
    "Brand Name": brand_name,
    "Class / Type": class_type,
    "Alcohol Content": alcohol_content,
    "Net Contents": net_contents,
    "Producer / Bottler Address": producer_address,
    "Country of Origin": country_of_origin,
    "Government Warning": government_warning,
}

st.subheader("Label Text")
st.info("For this first version, paste label text below. OCR upload will be added next.")

sample_text = """OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Old Tom Distillery, Louisville, KY
USA

GOVERNMENT WARNING: According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
"""

label_text = st.text_area("Paste extracted label text", sample_text, height=250)

if st.button("Verify Label", type="primary"):
    start_time = time.time()
    results = compare_label_fields(expected_fields, label_text)
    elapsed = round(time.time() - start_time, 2)

    df = pd.DataFrame(results)

    mismatch_count = len(df[df["Status"].isin(["Mismatch", "Missing / Unreadable"])])
    review_count = len(df[df["Status"] == "Possible Match, Human Review"])
    matched_count = len(df[df["Status"].isin(["Exact Match", "Normalized Match"])])

    if mismatch_count > 0:
        overall_status = "Reject Risk"
        recommendation = "One or more required fields appear mismatched or missing. Agent review is required before approval."
    elif review_count > 0:
        overall_status = "Human Review"
        recommendation = "One or more fields may match but require agent judgment."
    else:
        overall_status = "Likely Pass"
        recommendation = "All checked fields appear to match. Agent should complete final review."

    st.subheader("Agent Review Summary")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Status", overall_status)
    col2.metric("Matched Fields", matched_count)
    col3.metric("Needs Review", review_count + mismatch_count)
    col4.metric("Processing Time", f"{elapsed}s")

    st.write(f"**Recommended Action:** {recommendation}")

    st.subheader("Field-by-Field Results")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Review Results CSV",
        csv,
        "label_review_results.csv",
        "text/csv"
    )
