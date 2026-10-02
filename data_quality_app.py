import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="تحليل أنواع البيانات",
    layout="wide"
)

st.title("تحليل أنواع وحجم البيانات")

# رفع الملف
uploaded_file = st.file_uploader(
    "ارفع ملف البيانات",
    type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:

    # قراءة الملف
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("تم رفع الملف بنجاح")

    st.write("عدد السجلات:", f"{len(df):,}")
    st.write("عدد الحقول:", f"{len(df.columns):,}")

    # حقول التواريخ
    date_columns = [
        "تاريخ التعيين",
        "تاريخ الميلاد",
        "تاريخ انتهاء الدارسة",
        "تاريخ إنتهاء الهوية",
        "تاريخ اصدار الجواز",
        "تاريخ إنتهاء الجواز",
        "تاريخ اصدار اللإقامة",
        "تاريخ انتهاء اللإقامة"
    ]

    # تحويل حقول التواريخ
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce",
                dayfirst=True
            )

    # كم حقل تاريخ تم التعرف عليه
    found_dates = [col for col in date_columns if col in df.columns]

    st.info(
        f"تم التعرف على {len(found_dates)} حقول تاريخ وتحويلها إلى Date/Time"
    )

    # عرض الحقول التي تم تحويلها
    with st.expander("حقول التواريخ التي تم تحويلها"):
        for col in found_dates:
            st.write("•", col)

    # =========================
    # تصنيف كل قيمة
    # =========================

    def classify_value(value, column):

        if pd.isna(value):
            return "قيم مفقودة"

        if column in date_columns:
            return "بيانات تاريخية"

        if isinstance(value, (bool, np.bool_)):
            return "بيانات منطقية"

        if isinstance(value, (int, np.integer)):
            return "أرقام صحيحة"

        if isinstance(value, (float, np.floating)):
            return "أرقام عشرية"

        return "بيانات نصية"

    # =========================
    # حساب عدد القيم
    # =========================

    type_counts = {}

    for col in df.columns:

        for value in df[col]:

            data_type = classify_value(value, col)

            type_counts[data_type] = (
                type_counts.get(data_type, 0) + 1
            )

    summary = pd.DataFrame(
        list(type_counts.items()),
        columns=["نوع البيانات", "عدد القيم"]
    )

    total_values = summary["عدد القيم"].sum()

    summary["النسبة %"] = (
        summary["عدد القيم"] / total_values * 100
    ).round(2)

    # =========================
    # حجم البيانات
    # =========================

    total_bytes = df.memory_usage(
        index=True,
        deep=True
    ).sum()

    total_gb = total_bytes / (1024 ** 3)
    total_mb = total_bytes / (1024 ** 2)

    # =========================
    # مؤشرات رئيسية
    # =========================

    st.subheader("ملخص البيانات")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "عدد السجلات",
        f"{len(df):,}"
    )

    c2.metric(
        "عدد الحقول",
        f"{len(df.columns):,}"
    )

    c3.metric(
        "إجمالي القيم",
        f"{total_values:,}"
    )

    c4.metric(
        "حجم البيانات",
        f"{total_gb:.4f} GB"
    )

    st.caption(
        f"الحجم التقريبي في الذاكرة: "
        f"{total_mb:,.2f} MB"
    )

    # =========================
    # جدول أنواع البيانات
    # =========================

    st.subheader("توزيع أنواع البيانات")

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True
    )

    # =========================
    # الرسم البياني
    # =========================

    st.subheader("توزيع القيم حسب نوع البيانات")

    chart_data = (
        summary
        .set_index("نوع البيانات")["عدد القيم"]
    )

    st.bar_chart(chart_data)

    # =========================
    # معلومات الحقول
    # =========================

    st.subheader("هيكل البيانات")

    structure = pd.DataFrame({
        "اسم الحقل": df.columns,
        "نوع الحقل بعد المعالجة": [
            str(df[col].dtype)
            for col in df.columns
        ],
        "عدد القيم": [
            df[col].count()
            for col in df.columns
        ],
        "القيم المفقودة": [
            df[col].isna().sum()
            for col in df.columns
        ]
    })

    st.dataframe(
        structure,
        use_container_width=True,
        hide_index=True
    )
