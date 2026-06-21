import streamlit as st
import pandas as pd
from datetime import datetime
import cv2
import numpy as np
import easyocr  
import time
import io

# إعداد قارئ النصوص للغة العربية والإنجليزية
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ar', 'en'])

# إعداد واجهة المستخدم وتحديد الألوان المتناسقة مع الشعار الأخضر
st.set_page_config(page_title="مستخرج أوامر الصرف - باب الهوى", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #0d2823; 
        color: white;
    }
    h1, h2, h3, p, span, label {
        color: white !important;
    }
    .stButton>button {
        background-color: #baa07a; 
        color: #0d2823;
        font-weight: bold;
        width: 100%;
    }
    .dataframe {
        background-color: #123a33 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# إدارة حالة التطبيق
if "splash_done" not in st.session_state:
    st.session_state.splash_done = False

if "history_data" not in st.session_state:
    st.session_state.history_data = []

# شاشة بدء تشغيل التطبيق (Splash Screen)
if not st.session_state.splash_done:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("logo.jpg", use_container_width=True)
        except:
            st.warning("⚠️ يرجى وضع ملف logo.jpg في نفس المجلد لعرض الشعار.")
        st.markdown("<h3 style='text-align: center; color: #baa07a;'>جاري تحميل النظام...</h3>", unsafe_allow_html=True)
    time.sleep(3)
    st.session_state.splash_done = True
    st.rerun()

# واجهة التطبيق الرئيسية
reader = load_ocr()

st.title(" 📄 نظام أتمتة أوامر الصرف المالي")
st.subheader("الهيئة العامة للمنافذ والجمارك - منفذ باب الهوى")
st.write("قم بتصوير أمر الصرف لاستخراج البيانات وتصديرها إلى Excel")

today_date = datetime.now().strftime("%Y/%m/%d")
st.info(f"📅 تاريخ اليوم المستند: {today_date}")

image_file = st.camera_input("التقط صورة لأمر الصرف")

if image_file is not None:
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    opencv_image = cv2.imdecode(file_bytes, 1)
    
    st.image(opencv_image, channels="BGR", caption="الصورة التي تم التقاطها")
    
    with st.spinner("⏳ جاري قراءة الورقة واستخراج البيانات..."):
        result = reader.readtext(opencv_image, detail=0)
        full_text = " ".join(result)
        
        # استخراج رقم أمر الصرف
        order_number = ""
        for word in result:
            if word.isdigit() and len(word) >= 3 and len(word) <= 5 and word != "2026":
                order_number = word
                break

        # استخراج بيان النفقة
        expense_details = ""
        if "بيان النفقة" in full_text or "اصلاح" in full_text:
            for res in result:
                if "اصلاح" in res or "طرمبة" in res or "استبدال" in res:
                    expense_details = res
                    break

        # استخراج المبلغ الصافي
        net_amount = ""
        for res in reversed(result): 
            if res.isdigit() and int(res) > 100: 
                net_amount = res
                break

    # شاشة المراجعة والتعديل
    st.subheader("📝 مراجعة البيانات المستخرجة")
    
    final_date = st.text_input("تاريخ اليوم", today_date)
    final_order_num = st.text_input("رقم أمر الصرف", order_number)
    final_expense = st.text_area("بيان النفقة", expense_details)
    final_amount = st.text_input("المبلغ الصافي", net_amount)

    if st.button("💾 حفظ البيانات الحالية في السجل"):
        new_record = {
            "تاريخ اليوم": final_date,
            "رقم أمر صرف": final_order_num,
            "بيان النفقة": final_expense,
            "المبلغ الصافي": final_amount
        }
        st.session_state.history_data.append(new_record)
        st.success(f"✅ تم حفظ الأمر رقم ({final_order_num}) في السجل بنجاح!")

# قسم السجل المحفوظ
st.markdown("---")
st.header("🗂️ سجل المحفوظات")

if len(st.session_state.history_data) > 0:
    df_history = pd.DataFrame(st.session_state.history_data)
    st.dataframe(df_history, use_container_width=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_history.to_excel(writer, index=False, sheet_name='سجل أوامر الصرف')
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 تحميل السجل بالكامل (Excel)",
            data=buffer.getvalue(),
            file_name=f"سجل_أوامر_الصرف_{today_date.replace('/', '-')}.xlsx",
            mime="application/vnd.ms-excel"
        )
    with col2:
        if st.button("🗑️ مسح وإفراغ السجل"):
            st.session_state.history_data = []
            st.rerun()
else:
    st.warning("🔄 لا توجد أي بيانات محفوظة في السجل حالياً.")