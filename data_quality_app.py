import streamlit as st
import pandas as pd
import numpy as np
import re

# ============================================================
# إعداد الصفحة
# ============================================================

st.set_page_config(
    page_title="تحليل أنواع وحجم البيانات",
    page_icon="📊",
    layout="wide"
)

st.title("📊 تحليل أنواع وحجم البيانات الرئيسية")

st.write(
    """
    يقوم النظام بتنظيف البيانات، والتعرف على أنواع القيم الفعلية،
    وتحليل عدد وحجم وتوزيع البيانات وجودة اكتمالها.
    """
)


# ============================================================
# رفع الملف
# ============================================================

uploaded_file = st.file_uploader(
    "ارفع ملف البيانات",
    type=["xlsx", "xls", "csv"]
)


if uploaded_file is not None:

    # ========================================================
    # قراءة الملف
    # ========================================================

    try:

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

    except Exception as e:

        st.error(
            f"حدث خطأ أثناء قراءة الملف: {e}"
        )

        st.stop()


    st.success(
        "تم رفع الملف وقراءة البيانات بنجاح"
    )


    # ========================================================
    # دالة تنظيف النص
    # ========================================================

    def clean_text(text):

        if pd.isna(text):
            return text

        text = str(text)

        # إزالة علامات اتجاه النص المخفية
        text = re.sub(
            r'[\u200e\u200f\u202a-\u202e\u2066-\u2069]',
            '',
            text
        )

        # إزالة المسافات الخاصة
        text = text.replace(
            "\xa0",
            " "
        )

        return text.strip()


    # تنظيف أسماء الأعمدة
    df.columns = [
        clean_text(col)
        for col in df.columns
    ]


    # ========================================================
    # حقول التواريخ المعروفة
    # ========================================================

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


    # ========================================================
    # تحويل الأرقام العربية والفارسية
    # ========================================================

    arabic_digits = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩",
        "0123456789"
    )

    persian_digits = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹",
        "0123456789"
    )


    # ========================================================
    # تنظيف القيم
    # ========================================================

    def clean_value(value):

        if pd.isna(value):
            return np.nan

        if isinstance(value, str):

            # إزالة رموز الاتجاه
            value = re.sub(
                r'[\u200e\u200f\u202a-\u202e\u2066-\u2069]',
                '',
                value
            )

            # إزالة المسافات الخاصة
            value = value.replace(
                "\xa0",
                " "
            ).strip()

            # تحويل الأرقام العربية
            value = value.translate(
                arabic_digits
            )

            # تحويل الأرقام الفارسية
            value = value.translate(
                persian_digits
            )

            # قيم تعتبر فارغة
            empty_values = [
                "",
                "nan",
                "none",
                "null",
                "n/a",
                "na",
                "-"
            ]

            if value.lower() in empty_values:
                return np.nan

        return value


    # تنظيف كل البيانات
    for column in df.columns:

        df[column] = df[column].apply(
            clean_value
        )


    # ========================================================
    # توحيد أسماء الحقول
    # ========================================================

    def normalize_column_name(name):

        name = clean_text(name)

        replacements = {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ة": "ه"
        }

        for old, new in replacements.items():

            name = name.replace(
                old,
                new
            )

        name = re.sub(
            r"\s+",
            " ",
            name
        )

        return name.strip()


    # ========================================================
    # التعرف على حقول التاريخ
    # ========================================================

    normalized_date_names = {

        normalize_column_name(x)

        for x in date_columns
    }


    found_date_columns = []

    for column in df.columns:

        normalized_column = (
            normalize_column_name(
                column
            )
        )

        if (
            normalized_column
            in normalized_date_names
        ):

            found_date_columns.append(
                column
            )


    # ========================================================
    # التعرف على التاريخ من القيمة
    # ========================================================

    def is_date(value):

        if pd.isna(value):
            return False

        if isinstance(
            value,
            (
                pd.Timestamp,
                np.datetime64
            )
        ):
            return True

        if not isinstance(
            value,
            str
        ):
            return False

        value = value.strip()

        # صيغ التاريخ المقبولة
        patterns = [

            # 14/02/2008
            r'^\d{1,2}/\d{1,2}/\d{4}$',

            # 14-02-2008
            r'^\d{1,2}-\d{1,2}-\d{4}$',

            # 14.02.2008
            r'^\d{1,2}\.\d{1,2}\.\d{4}$',

            # 2008/02/14
            r'^\d{4}/\d{1,2}/\d{1,2}$',

            # 2008-02-14
            r'^\d{4}-\d{1,2}-\d{1,2}$'
        ]


        if not any(
            re.match(
                pattern,
                value
            )
            for pattern in patterns
        ):

            return False


        try:

            result = pd.to_datetime(
                value,
                dayfirst=True,
                errors="coerce"
            )

            return not pd.isna(
                result
            )

        except:

            return False


    # ========================================================
    # التعرف على Integer
    # ========================================================

    def is_integer(value):

        if pd.isna(value):
            return False

        if isinstance(
            value,
            (bool, np.bool_)
        ):
            return False


        if isinstance(
            value,
            (int, np.integer)
        ):
            return True


        if isinstance(
            value,
            (float, np.floating)
        ):

            return float(
                value
            ).is_integer()


        if isinstance(
            value,
            str
        ):

            test_value = (
                value
                .replace(",", "")
                .strip()
            )

            return bool(
                re.fullmatch(
                    r'[-+]?\d+',
                    test_value
                )
            )

        return False


    # ========================================================
    # التعرف على Decimal
    # ========================================================

    def is_decimal(value):

        if pd.isna(value):
            return False

        if isinstance(
            value,
            (bool, np.bool_)
        ):
            return False


        if isinstance(
            value,
            (float, np.floating)
        ):

            return not float(
                value
            ).is_integer()


        if isinstance(
            value,
            str
        ):

            test_value = (
                value
                .replace(",", "")
                .strip()
            )

            return bool(
                re.fullmatch(
                    r'[-+]?\d+\.\d+',
                    test_value
                )
            )

        return False


    # ========================================================
    # Boolean
    # ========================================================

    def is_boolean(value):

        if isinstance(
            value,
            (bool, np.bool_)
        ):

            return True


        if isinstance(
            value,
            str
        ):

            boolean_values = [

                "true",
                "false",

                "yes",
                "no",

                "نعم",
                "لا"
            ]

            return (
                value
                .strip()
                .lower()
                in boolean_values
            )

        return False


    # ========================================================
    # الحقول التعريفية
    # ========================================================

    identifier_keywords = [

        "رقم الموظف",

        "الرقم الوظيفي",

        "رقم الهوية",

        "رقم الهويه",

        "رقم الجواز",

        "رقم الاقامة",

        "رقم الإقامة",

        "رقم الهاتف",

        "رقم الموبايل",

        "الهاتف",

        "الموبايل",

        "رقم الملف"
    ]


    def is_identifier_column(
        column
    ):

        normalized = (
            normalize_column_name(
                column
            )
        )


        for keyword in identifier_keywords:

            normalized_keyword = (
                normalize_column_name(
                    keyword
                )
            )

            if (
                normalized_keyword
                in normalized
            ):

                return True

        return False


    # ========================================================
    # تصنيف كل قيمة
    # ========================================================

    def classify_value(
        value,
        column
    ):

        # --------------------------
        # القيم المفقودة
        # --------------------------

        if pd.isna(value):

            return "قيم مفقودة"


        # --------------------------
        # البيانات التعريفية
        # --------------------------

        if is_identifier_column(
            column
        ):

            return "بيانات تعريفية"


        # --------------------------
        # حقول التاريخ المحددة
        # --------------------------

        if column in found_date_columns:

            return "بيانات تاريخية"


        # --------------------------
        # تاريخ مكتشف تلقائياً
        # --------------------------

        if is_date(value):

            return "بيانات تاريخية"


        # --------------------------
        # Boolean
        # --------------------------

        if is_boolean(value):

            return "بيانات منطقية"


        # --------------------------
        # Integer
        # --------------------------

        if is_integer(value):

            return "أرقام صحيحة"


        # --------------------------
        # Decimal
        # --------------------------

        if is_decimal(value):

            return "أرقام عشرية"


        # --------------------------
        # Text
        # --------------------------

        return "بيانات نصية"


    # ========================================================
    # حساب الحجم المنطقي للقيمة
    # ========================================================

    def get_value_size(
        value,
        data_type
    ):

        if pd.isna(value):

            return 0


        # النصوص
        if data_type == "بيانات نصية":

            return len(
                str(value)
                .encode("utf-8")
            )


        # Identifiers
        elif data_type == "بيانات تعريفية":

            return len(
                str(value)
                .encode("utf-8")
            )


        # Integer
        elif data_type == "أرقام صحيحة":

            return 8


        # Float
        elif data_type == "أرقام عشرية":

            return 8


        # DateTime
        elif data_type == "بيانات تاريخية":

            return 8


        # Boolean
        elif data_type == "بيانات منطقية":

            return 1


        # أي نوع آخر
        return len(
            str(value)
            .encode("utf-8")
        )


    # ========================================================
    # تحليل جميع القيم
    # ========================================================

    stats = {}


    for column in df.columns:

        for value in df[column]:

            data_type = (
                classify_value(
                    value,
                    column
                )
            )


            size_bytes = (
                get_value_size(
                    value,
                    data_type
                )
            )


            if (
                data_type
                not in stats
            ):

                stats[
                    data_type
                ] = {

                    "count": 0,

                    "bytes": 0
                }


            stats[
                data_type
            ]["count"] += 1


            stats[
                data_type
            ]["bytes"] += (
                size_bytes
            )


    # ========================================================
    # إنشاء جدول النتائج
    # ========================================================

    results = []


    for (
        data_type,
        values
    ) in stats.items():


        results.append(
            {

                "نوع البيانات":
                    data_type,

                "عدد القيم":
                    values[
                        "count"
                    ],

                "الحجم Bytes":
                    values[
                        "bytes"
                    ]
            }
        )


    summary = pd.DataFrame(
        results
    )


    # ========================================================
    # إجماليات البيانات
    # ========================================================

    number_of_records = len(
        df
    )


    number_of_columns = len(
        df.columns
    )


    total_cells = (

        number_of_records
        *
        number_of_columns
    )


    missing_cells = int(

        df
        .isna()
        .sum()
        .sum()
    )


    filled_cells = (

        total_cells
        -
        missing_cells
    )


    # ========================================================
    # نسبة اكتمال البيانات
    # ========================================================

    if total_cells > 0:

        completion_rate = (

            filled_cells
            /
            total_cells
            *
            100
        )

    else:

        completion_rate = 0


    # ========================================================
    # حساب KB / MB / GB
    # ========================================================

    summary[
        "الحجم KB"
    ] = (

        summary[
            "الحجم Bytes"
        ]
        /
        1024
    )


    summary[
        "الحجم MB"
    ] = (

        summary[
            "الحجم Bytes"
        ]
        /
        (1024 ** 2)
    )


    summary[
        "الحجم GB"
    ] = (

        summary[
            "الحجم Bytes"
        ]
        /
        (1024 ** 3)
    )


    # ========================================================
    # إجمالي الحجم بدون Missing
    # ========================================================

    total_data_bytes = int(

        summary.loc[
            summary[
                "نوع البيانات"
            ]
            !=
            "قيم مفقودة",

            "الحجم Bytes"
        ]
        .sum()
    )


    # ========================================================
    # إجمالي KB / MB / GB
    # ========================================================

    total_kb = (
        total_data_bytes
        /
        1024
    )


    total_mb = (
        total_data_bytes
        /
        (1024 ** 2)
    )


    total_gb = (
        total_data_bytes
        /
        (1024 ** 3)
    )


    # ========================================================
    # نسبة كل نوع من القيم
    # ========================================================

    percentages = []


    for _, row in summary.iterrows():


        if (
            row[
                "نوع البيانات"
            ]
            ==
            "قيم مفقودة"
        ):

            percentage = (

                row[
                    "عدد القيم"
                ]
                /
                total_cells
                *
                100

            ) if total_cells else 0


        else:

            percentage = (

                row[
                    "عدد القيم"
                ]
                /
                filled_cells
                *
                100

            ) if filled_cells else 0


        percentages.append(
            round(
                percentage,
                2
            )
        )


    summary[
        "النسبة %"
    ] = percentages


    # ========================================================
    # نسبة الحجم
    # ========================================================

    if total_data_bytes > 0:

        summary[
            "نسبة الحجم %"
        ] = np.where(

            summary[
                "نوع البيانات"
            ]
            !=
            "قيم مفقودة",

            summary[
                "الحجم Bytes"
            ]
            /
            total_data_bytes
            *
            100,

            0
        )

    else:

        summary[
            "نسبة الحجم %"
        ] = 0


    summary[
        "نسبة الحجم %"
    ] = (

        summary[
            "نسبة الحجم %"
        ]
        .round(2)
    )


    # ========================================================
    # ترتيب الأنواع
    # ========================================================

    type_order = [

        "بيانات نصية",

        "بيانات تعريفية",

        "بيانات تاريخية",

        "أرقام صحيحة",

        "أرقام عشرية",

        "بيانات منطقية",

        "قيم مفقودة"
    ]


    order_map = {

        name: i

        for i, name
        in enumerate(
            type_order
        )
    }


    summary[
        "الترتيب"
    ] = (

        summary[
            "نوع البيانات"
        ]
        .map(
            order_map
        )
    )


    summary = (

        summary
        .sort_values(
            "الترتيب"
        )
        .drop(
            columns=[
                "الترتيب"
            ]
        )
    )


    # ========================================================
    # الملخص الرئيسي
    # ========================================================

    st.divider()

    st.header(
        "ملخص البيانات"
    )


    c1, c2, c3, c4 = (
        st.columns(4)
    )


    c1.metric(
        "عدد السجلات",
        f"{number_of_records:,}"
    )


    c2.metric(
        "عدد الحقول",
        f"{number_of_columns:,}"
    )


    c3.metric(
        "إجمالي الخلايا",
        f"{total_cells:,}"
    )


    c4.metric(
        "القيم المعبأة",
        f"{filled_cells:,}"
    )


    # ========================================================
    # الحجم الإجمالي بالثلاث وحدات
    # ========================================================

    st.subheader(
        "إجمالي حجم البيانات"
    )


    size1, size2, size3 = (
        st.columns(3)
    )


    size1.metric(
        "Kilobytes (KB)",
        f"{total_kb:,.2f} KB"
    )


    size2.metric(
        "Megabytes (MB)",
        f"{total_mb:,.4f} MB"
    )


    size3.metric(
        "Gigabytes (GB)",
        f"{total_gb:,.8f} GB"
    )


    # ========================================================
    # جودة البيانات
    # ========================================================

    st.divider()

    st.header(
        "جودة واكتمال البيانات"
    )


    q1, q2, q3 = (
        st.columns(3)
    )


    q1.metric(
        "القيم المعبأة",
        f"{filled_cells:,}"
    )


    q2.metric(
        "القيم المفقودة",
        f"{missing_cells:,}"
    )


    q3.metric(
        "نسبة اكتمال البيانات",
        f"{completion_rate:.2f}%"
    )


    # ========================================================
    # جدول توزيع أنواع البيانات
    # ========================================================

    st.divider()

    st.header(
        "توزيع البيانات حسب النوع"
    )


    display_summary = (

        summary[
            [
                "نوع البيانات",

                "عدد القيم",

                "النسبة %",

                "الحجم KB",

                "الحجم MB",

                "الحجم GB",

                "نسبة الحجم %"
            ]
        ]
        .copy()
    )


    # تقريب KB
    display_summary[
        "الحجم KB"
    ] = (

        display_summary[
            "الحجم KB"
        ]
        .round(2)
    )


    # تقريب MB
    display_summary[
        "الحجم MB"
    ] = (

        display_summary[
            "الحجم MB"
        ]
        .round(4)
    )


    # تقريب GB
    display_summary[
        "الحجم GB"
    ] = (

        display_summary[
            "الحجم GB"
        ]
        .round(8)
    )


    st.dataframe(
        display_summary,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # بطاقات لكل نوع بيانات
    # ========================================================

    st.divider()

    st.header(
        "مؤشرات أنواع البيانات"
    )


    actual_data = (

        summary[
            summary[
                "نوع البيانات"
            ]
            !=
            "قيم مفقودة"
        ]
    )


    for _, row in actual_data.iterrows():

        st.subheader(
            row[
                "نوع البيانات"
            ]
        )


        d1, d2, d3, d4, d5 = (
            st.columns(5)
        )


        d1.metric(
            "عدد القيم",
            f'{int(row["عدد القيم"]):,}'
        )


        d2.metric(
            "النسبة",
            f'{row["النسبة %"]:.2f}%'
        )


        d3.metric(
            "KB",
            f'{row["الحجم KB"]:,.2f}'
        )


        d4.metric(
            "MB",
            f'{row["الحجم MB"]:,.4f}'
        )


        d5.metric(
            "GB",
            f'{row["الحجم GB"]:,.8f}'
        )


    # ========================================================
    # حقول التاريخ
    # ========================================================

    st.divider()

    st.header(
        "حقول التواريخ"
    )


    with st.expander(
        "عرض حقول التواريخ التي تم التعرف عليها"
    ):


        if found_date_columns:


            for column in found_date_columns:

                st.write(
                    f"✓ {column}"
                )


        else:

            st.warning(
                "لم يتم العثور على حقول التواريخ المحددة."
            )


    # ========================================================
    # تحليل كل حقل
    # ========================================================

    st.divider()

    st.header(
        "تفاصيل الحقول"
    )


    field_results = []


    for column in df.columns:


        total = len(
            df[column]
        )


        missing = int(

            df[column]
            .isna()
            .sum()
        )


        filled = (
            total
            -
            missing
        )


        field_types = {}

        field_bytes = 0


        for value in df[column]:


            data_type = (
                classify_value(
                    value,
                    column
                )
            )


            if (
                data_type
                !=
                "قيم مفقودة"
            ):


                field_types[
                    data_type
                ] = (

                    field_types.get(
                        data_type,
                        0
                    )
                    +
                    1
                )


                field_bytes += (
                    get_value_size(
                        value,
                        data_type
                    )
                )


        # النوع الرئيسي للحقل
        if field_types:


            main_type = max(
                field_types,
                key=field_types.get
            )


        else:

            main_type = "فارغ"


        # أحجام الحقل
        field_kb = (
            field_bytes
            /
            1024
        )


        field_mb = (
            field_bytes
            /
            (1024 ** 2)
        )


        field_gb = (
            field_bytes
            /
            (1024 ** 3)
        )


        # نسبة الاكتمال
        field_completion = (

            filled
            /
            total
            *
            100

        ) if total else 0


        field_results.append(
            {

                "اسم الحقل":
                    column,

                "النوع الرئيسي":
                    main_type,

                "عدد القيم":
                    filled,

                "القيم المفقودة":
                    missing,

                "نسبة الاكتمال %":
                    round(
                        field_completion,
                        2
                    ),

                "الحجم KB":
                    round(
                        field_kb,
                        2
                    ),

                "الحجم MB":
                    round(
                        field_mb,
                        4
                    ),

                "الحجم GB":
                    round(
                        field_gb,
                        8
                    )
            }
        )


    field_summary = (
        pd.DataFrame(
            field_results
        )
    )


    st.dataframe(
        field_summary,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # معاينة البيانات
    # ========================================================

    st.divider()

    with st.expander(
        "معاينة البيانات بعد التنظيف"
    ):

        st.dataframe(
            df.head(100),
            use_container_width=True
        )


    # ========================================================
    # تنزيل نتائج أنواع البيانات
    # ========================================================

    st.divider()

    st.header(
        "تحميل النتائج"
    )


    csv_data = (

        display_summary
        .to_csv(
            index=False
        )
        .encode(
            "utf-8-sig"
        )
    )


    st.download_button(

        label=
        "تحميل تحليل أنواع البيانات",

        data=
        csv_data,

        file_name=
        "data_type_analysis.csv",

        mime=
        "text/csv"
    )


    # ========================================================
    # تنزيل تفاصيل الحقول
    # ========================================================

    field_csv = (

        field_summary
        .to_csv(
            index=False
        )
        .encode(
            "utf-8-sig"
        )
    )


    st.download_button(

        label=
        "تحميل تحليل الحقول",

        data=
        field_csv,

        file_name=
        "field_analysis.csv",

        mime=
        "text/csv"
    )


else:

    st.info(
        "ارفع ملف Excel أو CSV لبدء تحليل البيانات."
    )
