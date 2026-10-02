import streamlit as st
import pandas as pd
import numpy as np
import re
import sys
from io import BytesIO

st.set_page_config(
    page_title="تحليل أنواع البيانات",
    layout="wide"
)

st.title("تحليل أنواع وحجم البيانات الرئيسية")

# =========================================================
# 1. رفع الملف
# =========================================================

uploaded_file = st.file_uploader(
    "ارفع ملف البيانات",
    type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:

    # =====================================================
    # 2. قراءة الملف
    # =====================================================

    if uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(
            uploaded_file,
            dtype=object
        )
    else:
        df = pd.read_excel(
            uploaded_file,
            dtype=object
        )

    st.success("تم رفع الملف بنجاح")

    # =====================================================
    # 3. حقول التواريخ المعروفة
    # =====================================================

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

    # =====================================================
    # 4. تنظيف النصوص والرموز المخفية
    # =====================================================

    def clean_value(value):

        if pd.isna(value):
            return value

        if isinstance(value, str):

            value = value.strip()

            # إزالة Unicode Direction Marks
            # مثل القيمة:
            # ‭14/02/2008‬
            value = re.sub(
                r'[\u200e\u200f\u202a-\u202e\u2066-\u2069]',
                '',
                value
            )

            # إزالة المسافات غير الطبيعية
            value = value.replace(
                '\xa0',
                ' '
            ).strip()

            # تحويل الأرقام العربية إلى إنجليزية
            arabic_numbers = str.maketrans(
                "٠١٢٣٤٥٦٧٨٩",
                "0123456789"
            )

            value = value.translate(
                arabic_numbers
            )

            # تحويل الأرقام الفارسية كذلك
            persian_numbers = str.maketrans(
                "۰۱۲۳۴۵۶۷۸۹",
                "0123456789"
            )

            value = value.translate(
                persian_numbers
            )

            if value == "":
                return np.nan

        return value


    # تنظيف جميع القيم
    for col in df.columns:

        df[col] = df[col].apply(
            clean_value
        )

    # =====================================================
    # 5. دالة التعرف على التاريخ
    # =====================================================

    def is_date(value):

        if pd.isna(value):
            return False

        # إذا Python معرفه أصلاً كتاريخ
        if isinstance(
            value,
            (
                pd.Timestamp,
                np.datetime64
            )
        ):
            return True

        if not isinstance(value, str):
            return False

        value = value.strip()

        # أشكال التاريخ التي نسمح بها
        date_patterns = [

            # 14/02/2008
            r'^\d{1,2}/\d{1,2}/\d{4}$',

            # 14-02-2008
            r'^\d{1,2}-\d{1,2}-\d{4}$',

            # 2008/02/14
            r'^\d{4}/\d{1,2}/\d{1,2}$',

            # 2008-02-14
            r'^\d{4}-\d{1,2}-\d{1,2}$'
        ]

        for pattern in date_patterns:

            if re.match(pattern, value):

                try:

                    pd.to_datetime(
                        value,
                        dayfirst=True,
                        errors="raise"
                    )

                    return True

                except:
                    return False

        return False


    # =====================================================
    # 6. التعرف على Integer
    # =====================================================

    def is_integer(value):

        if pd.isna(value):
            return False

        # رقم Python
        if isinstance(
            value,
            (int, np.integer)
        ):

            if isinstance(
                value,
                (bool, np.bool_)
            ):
                return False

            return True

        # رقم مخزن كنص
        if isinstance(value, str):

            value = value.strip()

            # إزالة الفواصل
            test_value = value.replace(
                ",",
                ""
            )

            return bool(
                re.match(
                    r'^[-+]?\d+$',
                    test_value
                )
            )

        return False


    # =====================================================
    # 7. التعرف على Decimal
    # =====================================================

    def is_decimal(value):

        if pd.isna(value):
            return False

        if isinstance(
            value,
            (float, np.floating)
        ):

            return True

        if isinstance(value, str):

            value = value.strip()

            test_value = value.replace(
                ",",
                ""
            )

            return bool(
                re.match(
                    r'^[-+]?\d+\.\d+$',
                    test_value
                )
            )

        return False


    # =====================================================
    # 8. Boolean
    # =====================================================

    def is_boolean(value):

        if isinstance(
            value,
            (bool, np.bool_)
        ):
            return True

        if isinstance(value, str):

            boolean_values = [
                "true",
                "false",
                "yes",
                "no",
                "نعم",
                "لا"
            ]

            return (
                value.strip().lower()
                in boolean_values
            )

        return False


    # =====================================================
    # 9. تحديد نوع كل قيمة
    # =====================================================

    def classify_value(value, column):

        # -------------------------
        # فارغ
        # -------------------------

        if pd.isna(value):
            return "قيم مفقودة"

        # -------------------------
        # حقول التاريخ المعروفة
        # -------------------------

        if column in date_columns:
            return "بيانات تاريخية"

        # -------------------------
        # تاريخ مكتشف تلقائياً
        # -------------------------

        if is_date(value):
            return "بيانات تاريخية"

        # -------------------------
        # Boolean
        # -------------------------

        if is_boolean(value):
            return "بيانات منطقية"

        # -------------------------
        # Integer
        # -------------------------

        if is_integer(value):
            return "أرقام صحيحة"

        # -------------------------
        # Decimal
        # -------------------------

        if is_decimal(value):
            return "أرقام عشرية"

        # -------------------------
        # الباقي نص
        # -------------------------

        return "بيانات نصية"


    # =====================================================
    # 10. تحويل القيمة فعلياً لنوعها الصحيح
    # =====================================================

    def convert_value(value, data_type):

        if pd.isna(value):
            return value

        try:

            if data_type == "بيانات تاريخية":

                return pd.to_datetime(
                    value,
                    dayfirst=True,
                    errors="coerce"
                )

            elif data_type == "أرقام صحيحة":

                if isinstance(value, str):
                    value = value.replace(",", "")

                return int(float(value))

            elif data_type == "أرقام عشرية":

                if isinstance(value, str):
                    value = value.replace(",", "")

                return float(value)

            elif data_type == "بيانات منطقية":

                if isinstance(value, bool):
                    return value

                true_values = [
                    "true",
                    "yes",
                    "نعم"
                ]

                return (
                    str(value)
                    .strip()
                    .lower()
                    in true_values
                )

            else:

                return str(value)

        except:

            return value


    # =====================================================
    # 11. تحليل جميع القيم
    # =====================================================

    stats = {}

    for column in df.columns:

        for value in df[column]:

            data_type = classify_value(
                value,
                column
            )

            converted_value = convert_value(
                value,
                data_type
            )

            # الحجم بعد تعريف القيمة بشكل صحيح
            if pd.isna(converted_value):

                size_bytes = 0

            else:

                try:
                    size_bytes = sys.getsizeof(
                        converted_value
                    )

                except:
                    size_bytes = 0

            if data_type not in stats:

                stats[data_type] = {
                    "count": 0,
                    "bytes": 0
                }

            stats[data_type]["count"] += 1
            stats[data_type]["bytes"] += size_bytes


    # =====================================================
    # 12. إنشاء ملخص
    # =====================================================

    results = []

    for data_type, values in stats.items():

        results.append({

            "نوع البيانات":
                data_type,

            "عدد القيم":
                values["count"],

            "الحجم Bytes":
                values["bytes"]
        })


    summary = pd.DataFrame(results)

    # =====================================================
    # 13. حساب الأحجام
    # =====================================================

    summary["الحجم MB"] = (
        summary["الحجم Bytes"]
        / (1024 ** 2)
    )

    summary["الحجم GB"] = (
        summary["الحجم Bytes"]
        / (1024 ** 3)
    )

    total_count = summary[
        "عدد القيم"
    ].sum()

    total_bytes = summary[
        "الحجم Bytes"
    ].sum()

    # =====================================================
    # 14. النسب
    # =====================================================

    summary["نسبة القيم %"] = (
        summary["عدد القيم"]
        / total_count
        * 100
    )

    if total_bytes > 0:

        summary["نسبة الحجم %"] = (
            summary["الحجم Bytes"]
            / total_bytes
            * 100
        )

    else:

        summary["نسبة الحجم %"] = 0

    # =====================================================
    # 15. تقريب
    # =====================================================

    summary["الحجم MB"] = (
        summary["الحجم MB"]
        .round(3)
    )

    summary["الحجم GB"] = (
        summary["الحجم GB"]
        .round(6)
    )

    summary["نسبة القيم %"] = (
        summary["نسبة القيم %"]
        .round(2)
    )

    summary["نسبة الحجم %"] = (
        summary["نسبة الحجم %"]
        .round(2)
    )

    summary = summary.sort_values(
        "الحجم Bytes",
        ascending=False
    )

    # =====================================================
    # 16. المؤشرات
    # =====================================================

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
        f"{total_count:,}"
    )

    c4.metric(
        "إجمالي الحجم",
        f"{total_bytes / (1024 ** 3):,.6f} GB"
    )

    # =====================================================
    # 17. جدول النتيجة
    # =====================================================

    st.subheader(
        "توزيع البيانات حسب النوع"
    )

    display_summary = summary[
        [
            "نوع البيانات",
            "عدد القيم",
            "نسبة القيم %",
            "الحجم MB",
            "الحجم GB",
            "نسبة الحجم %"
        ]
    ]

    st.dataframe(
        display_summary,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # 18. بطاقات
    # =====================================================

    st.subheader(
        "حجم كل نوع من البيانات"
    )

    for _, row in summary.iterrows():

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "نوع البيانات",
                row["نوع البيانات"]
            )

        with c2:

            st.metric(
                "عدد القيم",
                f'{int(row["عدد القيم"]):,}'
            )

        with c3:

            st.metric(
                "الحجم",
                f'{row["الحجم GB"]:.6f} GB'
            )

    # =====================================================
    # 19. حقول التاريخ المعروفة الموجودة
    # =====================================================

    found_dates = [
        col
        for col in date_columns
        if col in df.columns
    ]

    with st.expander(
        "حقول التواريخ المعرفة مسبقاً"
    ):

        for col in found_dates:
            st.write("•", col)

    # =====================================================
    # 20. تحميل التقرير
    # =====================================================

    csv = display_summary.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )

    st.download_button(
        "تحميل نتائج التحليل",
        data=csv,
        file_name="data_type_analysis.csv",
        mime="text/csv"
    )
