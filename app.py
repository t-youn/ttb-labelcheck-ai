import io
import os
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

# Apply pending autofill values now, before any widgets are instantiated.
# Streamlit raises an error if you write to a widget's session_state key after
# the widget has already been created in the same run. By draining the staging
# key here (at the very top, pre-widgets), the sf_* keys are safe to write.
if "pending_autofill" in st.session_state:
    for _k, _v in st.session_state.pop("pending_autofill").items():
        st.session_state[_k] = _v

tab_single, tab_batch = st.tabs(["Single Label Review", "Batch Review Queue"])


with tab_single:
    with st.sidebar:
        st.header("Application Fields")
        # Show a notice when fields were autofilled from an uploaded image
        if st.session_state.get("sf_autofill_active"):
            _src_label = "sample image" if st.session_state.get("sf_image_source") == "sample" else "uploaded label"
            st.info(f"Fields below were autofilled from the {_src_label}. Review carefully before verifying.")
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

        _demo_dir = "sample_data/demo_images"
        _sample_files = sorted([
            f for f in os.listdir(_demo_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]) if os.path.isdir(_demo_dir) else []

        if _sample_files:
            _preferred = "approved_beer_label_02.png"
            _options = ["(none)"] + _sample_files
            _default_idx = _options.index(_preferred) if _preferred in _options else 0
            _sample_sel = st.selectbox(
                "Or choose a sample label image",
                options=_options,
                index=_default_idx,
                key="sf_sample_choice",
            )
            st.caption(
                "Sample 02 is recommended for OCR/autofill testing. "
                "Sample 01 demonstrates lower-quality OCR behavior."
            )
        else:
            _sample_sel = "(none)"

        manual_text = st.text_area(
            "Fallback: paste label text if OCR is unavailable or unclear",
            "",
            height=180,
        )

        # Uploaded file takes priority over sample choice
        _active_bytes = None
        _active_caption = None
        _active_id = None

        if uploaded_file is not None:
            _active_bytes = uploaded_file.getvalue()
            _active_caption = f"Uploaded: {uploaded_file.name}"
            _active_id = f"{uploaded_file.name}_{uploaded_file.size}"
        elif _sample_sel != "(none)":
            _sample_path = os.path.join(_demo_dir, _sample_sel)
            with open(_sample_path, "rb") as _f:
                _active_bytes = _f.read()
            _active_caption = f"Sample image: {_sample_sel}"
            _active_id = f"sample_{_sample_sel}"

        _is_sample = uploaded_file is None and _sample_sel != "(none)"

        if _active_bytes is not None:
            if st.session_state.get("sf_last_file_id") != _active_id:
                _spinner_label = "Processing sample label image..." if _is_sample else "Processing label image..."
                with st.spinner(_spinner_label):
                    img_start = time.time()
                    image = Image.open(io.BytesIO(_active_bytes))
                    ocr_text, ocr_error = extract_text_from_image(io.BytesIO(_active_bytes))
                    quality = assess_image_quality(image, ocr_text or "")
                    img_elapsed = round(time.time() - img_start, 2)

                if ocr_text:
                    extracted = extract_fields_from_text(ocr_text)
                    autofill_map = {
                        "sf_brand_name": extracted.get("brand_name"),
                        "sf_class_type": extracted.get("class_type"),
                        "sf_alcohol_content": extracted.get("alcohol_content"),
                        "sf_net_contents": extracted.get("net_contents"),
                        "sf_country_of_origin": extracted.get("country_of_origin"),
                        "sf_government_warning": extracted.get("government_warning"),
                    }
                    bottler = ", ".join(filter(None, [
                        extracted.get("bottler_name"),
                        extracted.get("bottler_location"),
                    ]))
                    if bottler:
                        autofill_map["sf_producer_address"] = bottler
                    # Stage values for the next rerun; applied before widgets are created
                    st.session_state["pending_autofill"] = {
                        k: v for k, v in autofill_map.items() if v
                    }

                st.session_state["sf_last_file_id"] = _active_id
                st.session_state["sf_ocr_result"] = (ocr_text or "", ocr_error)
                st.session_state["sf_quality"] = quality
                st.session_state["sf_img_elapsed"] = img_elapsed
                st.session_state["sf_autofill_active"] = bool(ocr_text)
                st.session_state["sf_image_source"] = "sample" if _is_sample else "upload"
                st.rerun()

            ocr_text, ocr_error = st.session_state.get("sf_ocr_result", ("", None))
            quality = st.session_state.get("sf_quality", {})
            img_elapsed = st.session_state.get("sf_img_elapsed", 0)
            image_source = st.session_state.get("sf_image_source", "upload")

            if image_source == "sample":
                st.info("Using included sample image")

            st.image(io.BytesIO(_active_bytes), caption=_active_caption, use_container_width=True)
            st.caption(f"Processed in {img_elapsed}s")

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
                char_count = len(ocr_text)
                src_label = "sample image" if image_source == "sample" else "uploaded label"
                st.success(
                    f"OCR extracted {char_count} characters from the {src_label}. "
                    "Sidebar fields have been autofilled — review carefully before verifying."
                )
                with st.expander("View extracted OCR text"):
                    st.text(ocr_text)
            else:
                _no_ocr_msg = "OCR ran but did not detect readable text. Use paste fallback."
                if image_source == "sample":
                    _no_ocr_msg += " Try Sample 02 for better OCR results."
                st.warning(_no_ocr_msg)

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