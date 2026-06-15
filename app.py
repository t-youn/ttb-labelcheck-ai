import io
import time

import pandas as pd
import streamlit as st
from PIL import Image

from src.extraction import extract_fields_from_text
from src.image_quality import assess_image_quality
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


# Initialize sidebar field defaults in session state so autofill can update them
# before the sidebar widgets render on the next rerun.
_SIDEBAR_DEFAULTS = {
    "sf_brand_name": "OLD TOM DISTILLERY",
    "sf_class_type": "Kentucky Straight Bourbon Whiskey",
    "sf_alcohol_content": "45% Alc./Vol.",
    "sf_net_contents": "750 mL",
    "sf_producer_address": "Old Tom Distillery, Louisville, KY",
    "sf_country_of_origin": "USA",
    "sf_government_warning": DEFAULT_WARNING,
}
for _k, _v in _SIDEBAR_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

tab_single, tab_batch = st.tabs(["Single Label Review", "Batch Review Queue"])


with tab_single:
    with st.sidebar:
        st.header("Application Fields")
        # Show a notice when fields were autofilled from an uploaded image
        if st.session_state.get("sf_autofill_active"):
            st.info("Fields below were autofilled from the uploaded label. Review carefully before verifying.")
        brand_name = st.text_input("Brand Name", key="sf_brand_name")
        class_type = st.text_input("Class / Type", key="sf_class_type")
        alcohol_content = st.text_input("Alcohol Content", key="sf_alcohol_content")
        net_contents = st.text_input("Net Contents", key="sf_net_contents")
        producer_address = st.text_input("Producer / Bottler Address", key="sf_producer_address")
        country_of_origin = st.text_input("Country of Origin", key="sf_country_of_origin")
        government_warning = st.text_area("Government Warning", key="sf_government_warning")

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
            "Upload Label Artwork",
            type=["png", "jpg", "jpeg"],
        )

        manual_text = st.text_area(
            "Fallback: paste label text if OCR is unavailable or unclear",
            "",
            height=180,
        )

        if uploaded_file is not None:
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"

            if st.session_state.get("sf_last_file_id") != file_id:
                # New image — run OCR, quality assessment, and field extraction
                img_bytes = uploaded_file.getvalue()
                with st.spinner("Processing label image..."):
                    img_start = time.time()
                    image = Image.open(io.BytesIO(img_bytes))
                    ocr_text, ocr_error = extract_text_from_image(io.BytesIO(img_bytes))
                    quality = assess_image_quality(image, ocr_text or "")
                    img_elapsed = round(time.time() - img_start, 2)

                if ocr_text:
                    extracted = extract_fields_from_text(ocr_text)
                    # Push non-empty extracted values into sidebar field session state keys
                    autofill_map = {
                        "sf_brand_name": extracted.get("brand_name"),
                        "sf_class_type": extracted.get("class_type"),
                        "sf_alcohol_content": extracted.get("alcohol_content"),
                        "sf_net_contents": extracted.get("net_contents"),
                        "sf_country_of_origin": extracted.get("country_of_origin"),
                        "sf_government_warning": extracted.get("government_warning"),
                    }
                    # Combine bottler name and location into the single address field
                    bottler = ", ".join(filter(None, [
                        extracted.get("bottler_name"),
                        extracted.get("bottler_location"),
                    ]))
                    if bottler:
                        autofill_map["sf_producer_address"] = bottler
                    for k, v in autofill_map.items():
                        if v:
                            st.session_state[k] = v

                st.session_state["sf_last_file_id"] = file_id
                st.session_state["sf_ocr_result"] = (ocr_text or "", ocr_error)
                st.session_state["sf_quality"] = quality
                st.session_state["sf_img_elapsed"] = img_elapsed
                # Only show autofill notice if OCR actually produced text
                st.session_state["sf_autofill_active"] = bool(ocr_text)
                st.rerun()

            # Retrieve cached results from session state (populated on prior rerun)
            ocr_text, ocr_error = st.session_state.get("sf_ocr_result", ("", None))
            quality = st.session_state.get("sf_quality", {})
            img_elapsed = st.session_state.get("sf_img_elapsed", 0)

            st.image(uploaded_file, caption="Uploaded label", use_container_width=True)
            st.caption(f"Processed in {img_elapsed}s")

            # Image quality assessment
            if quality:
                score = quality["score"]
                qlabel = quality["status"]
                rec = quality["recommendation"]
                msg = f"Image Quality: **{qlabel}** ({score}/100) — {rec}"
                if qlabel in ("Excellent", "Good"):
                    st.success(msg)
                elif qlabel == "Fair":
                    st.warning(msg)
                else:
                    st.error(msg)

            if ocr_error:
                st.warning(ocr_error)
            elif ocr_text:
                st.success("OCR extracted text from the label. Sidebar fields have been autofilled.")
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