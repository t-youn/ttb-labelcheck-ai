import time
import pandas as pd
import streamlit as st

from src.matching import compare_label_fields
from src.ocr import extract_text_from_image

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

DEFAULT_WARNING = (
    "GOVERNMENT WARNING: According to the Surgeon General, women should not drink "
    "alcoholic beverages during pregnancy because of the risk of birth defects. "
    "Consumption of alcoholic beverages impairs your ability to drive a car or operate "
    "machinery, and may cause health problems."
)

SAMPLE_TEXT = f"""OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Old Tom Distillery, Louisville, KY
USA

{DEFAULT_WARNING}
"""


def build_expected_fields(
    brand_name,
    class_type,
    alcohol_content,
    net_contents,
    producer_address,
    country_of_origin,
    government_warning,
):
    return {
        "Brand Name": brand_name,
        "Class / Type": class_type,
        "Alcohol Content": alcohol_content,
        "Net Contents": net_contents,
        "Producer / Bottler Address": producer_address,
        "Country of Origin": country_of_origin,
        "Government Warning": government_warning,
    }


def summarize_results(results, elapsed):
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

    return df, overall_status, recommendation, matched_count, review_count, mismatch_count, elapsed


tab_single, tab_batch = st.tabs(["Single Label Review", "Batch Review Queue"])


with tab_single:
    with st.sidebar:
        st.header("Application Fields")
        brand_name = st.text_input("Brand Name", "OLD TOM DISTILLERY")
        class_type = st.text_input("Class / Type", "Kentucky Straight Bourbon Whiskey")
        alcohol_content = st.text_input("Alcohol Content", "45% Alc./Vol.")
        net_contents = st.text_input("Net Contents", "750 mL")
        producer_address = st.text_input("Producer / Bottler Address", "Old Tom Distillery, Louisville, KY")
        country_of_origin = st.text_input("Country of Origin", "USA")
        government_warning = st.text_area("Government Warning", DEFAULT_WARNING)

    expected_fields = build_expected_fields(
        brand_name,
        class_type,
        alcohol_content,
        net_contents,
        producer_address,
        country_of_origin,
        government_warning,
    )

    st.subheader("Label Input")

    input_mode = st.radio(
        "Choose label input method",
        ["Upload label image", "Paste label text"],
        horizontal=True
    )

    ocr_text = ""
    ocr_error = None

    if input_mode == "Upload label image":
        uploaded_file = st.file_uploader(
            "Upload label artwork",
            type=["png", "jpg", "jpeg"]
        )

        manual_text = st.text_area(
            "Optional fallback: paste label text if OCR is unavailable or unclear",
            "",
            height=180
        )

        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded label", use_container_width=True)
            ocr_text, ocr_error = extract_text_from_image(uploaded_file)

            if ocr_error:
                st.warning(ocr_error)
            elif ocr_text:
                st.success("OCR extracted text successfully.")
                with st.expander("View extracted OCR text"):
                    st.text(ocr_text)

        label_text = ocr_text if ocr_text else manual_text

    else:
        label_text = st.text_area("Paste extracted label text", SAMPLE_TEXT, height=250)

    if st.button("Verify Label", type="primary"):
        if not label_text.strip():
            st.error("No label text available. Upload a readable image or paste label text manually.")
            st.stop()

        start_time = time.time()
        results = compare_label_fields(expected_fields, label_text)
        elapsed = round(time.time() - start_time, 2)

        df, overall_status, recommendation, matched_count, review_count, mismatch_count, elapsed = summarize_results(results, elapsed)

        st.subheader("Agent Review Summary")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Overall Status", overall_status)
        col2.metric("Matched Fields", matched_count)
        col3.metric("Needs Review", review_count + mismatch_count)
        col4.metric("Processing Time", f"{elapsed}s")

        st.write(f"**Recommended Action:** {recommendation}")

        st.subheader("Field-by-Field Results")
        st.dataframe(df, use_container_width=True)

        with st.expander("Raw label text used for verification"):
            st.text(label_text)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Review Results CSV",
            csv,
            "label_review_results.csv",
            "text/csv"
        )


with tab_batch:
    st.subheader("Batch Review Queue")
    st.markdown("""
    Upload a CSV containing expected application fields and label text.
    This simulates high-volume importer submissions and creates a review queue for agents.
    """)

    st.info("For this prototype, batch mode uses a `label_text` column. Image batch OCR can be added in a future version.")

    if "batch_df" not in st.session_state:
        st.session_state["batch_df"] = None

    use_sample_batch = st.button("Use built-in sample batch")

    batch_file = st.file_uploader(
        "Upload your own batch CSV",
        type=["csv"],
        key="batch_csv"
    )

    st.caption("Required columns: brand_name, class_type, alcohol_content, net_contents, producer_address, country_of_origin, government_warning, label_text")

    if use_sample_batch:
        st.session_state["batch_df"] = pd.read_csv("sample_data/application_batch.csv")
        st.success("Built-in sample batch loaded.")

    elif batch_file is not None:
        st.session_state["batch_df"] = pd.read_csv(batch_file)
        st.success("Uploaded batch loaded.")

    batch_df = st.session_state["batch_df"]

    if batch_df is not None:
        required_columns = [
            "brand_name",
            "class_type",
            "alcohol_content",
            "net_contents",
            "producer_address",
            "country_of_origin",
            "government_warning",
            "label_text",
        ]

        missing_columns = [col for col in required_columns if col not in batch_df.columns]

        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.stop()

        st.write(f"Loaded {len(batch_df)} sample application records.")

        if st.button("Run Batch Verification", type="primary"):
            queue_results = []
            detailed_results = []

            for index, row in batch_df.iterrows():
                start_time = time.time()

                expected_fields = build_expected_fields(
                    row.get("brand_name", ""),
                    row.get("class_type", ""),
                    row.get("alcohol_content", ""),
                    row.get("net_contents", ""),
                    row.get("producer_address", ""),
                    row.get("country_of_origin", ""),
                    row.get("government_warning", ""),
                )

                label_text = row.get("label_text", "")
                results = compare_label_fields(expected_fields, label_text)
                elapsed = round(time.time() - start_time, 2)

                result_df, overall_status, recommendation, matched_count, review_count, mismatch_count, elapsed = summarize_results(results, elapsed)

                filename = row.get("filename", f"row_{index + 1}")

                queue_results.append({
                    "Filename": filename,
                    "Overall Status": overall_status,
                    "Matched Fields": matched_count,
                    "Needs Review": review_count + mismatch_count,
                    "Processing Time": elapsed,
                    "Recommended Action": recommendation,
                })

                for item in results:
                    detailed_results.append({
                        "Filename": filename,
                        "Field": item["Field"],
                        "Application Value": item["Application Value"],
                        "Status": item["Status"],
                        "Explanation": item["Explanation"],
                    })

            queue_df = pd.DataFrame(queue_results)
            detailed_df = pd.DataFrame(detailed_results)

            st.subheader("Review Queue Summary")
            st.dataframe(queue_df, width="stretch")

            st.subheader("Detailed Batch Results")
            st.dataframe(detailed_df, width="stretch")

            st.download_button(
                "Download Batch Queue CSV",
                queue_df.to_csv(index=False).encode("utf-8"),
                "batch_review_queue.csv",
                "text/csv"
            )

            st.download_button(
                "Download Detailed Batch Results CSV",
                detailed_df.to_csv(index=False).encode("utf-8"),
                "batch_detailed_results.csv",
                "text/csv"
            )

    else:
        st.markdown("Use the built-in sample batch or upload your own CSV to test batch mode.")