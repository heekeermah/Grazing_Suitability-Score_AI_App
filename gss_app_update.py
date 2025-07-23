import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import os
import traceback
from gtts import gTTS
import tempfile

# ========== TTS Module ==========
def play_voice(score, language):
    recommendation = get_recommendation(score, language)
    tts = gTTS(text=recommendation, lang='ha' if language == 'Hausa' else 'en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
        tts.save(tmpfile.name)
        st.sidebar.audio(tmpfile.name)

# ========== AI Recommendation Helper ==========
def get_recommendation(score, language):
    if score < 0.3:
        return "This plot is not suitable for grazing. Water is limited and vegetation is poor." if language == "English" else "Wannan fili bai dace da kiwo ba. Babu ruwan sha sosai, kuma ganyen ciyawa ya ragu."
    elif score < 0.5:
        return "This plot can be grazed cautiously. Monitor livestock load." if language == "English" else "Za a iya kiwo a hankali a wannan fili. Amma a kula da yawancin shanu da za a kai."
    else:
        return "This is a very suitable plot for grazing. Water and forage are sufficient." if language == "English" else "Wannan fili yana da kyau sosai don kiwo. Ruwan sha da ciyawa sun isa."

# ========== GSS Calculation ==========
def calculate_gss(df, weights=None):
    try:
        if weights is None:
            weights = {
                'biomass': 0.4,
                'shrub': 0.2,
                'grazing': 0.2,
                'woody': 0.2
            }

        data = df[['available_biomass', 'Shrub %', 'grazing_pressure', 'total woody count']].copy()

        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(data)
        scaled_df = pd.DataFrame(scaled, columns=['biomass_score', 'shrub_raw', 'grazing_raw', 'woody_raw'])

        scaled_df['shrub_score'] = 1 - scaled_df['shrub_raw']
        scaled_df['grazing_score'] = 1 - scaled_df['grazing_raw']
        scaled_df['woody_score'] = 1 - scaled_df['woody_raw']

        scaled_df['GSS'] = (
            weights['biomass'] * scaled_df['biomass_score'] +
            weights['shrub'] * scaled_df['shrub_score'] +
            weights['grazing'] * scaled_df['grazing_score'] +
            weights['woody'] * scaled_df['woody_score']
        )

        def diagnose(row):
            if row.GSS < 0.3:
                if row.shrub_raw > 0.7:
                    return "Too much shrub cover"
                elif row.grazing_raw > 0.7:
                    return "Excessive grazing pressure"
                elif row.woody_raw > 0.7:
                    return "High woody plant density"
                else:
                    return "Very low biomass"
            elif row.GSS < 0.5:
                return "Poor condition, needs intervention"
            elif row.GSS < 0.75:
                return "Moderately suitable"
            else:
                return "Highly suitable"

        scaled_df['Diagnosis'] = scaled_df.apply(diagnose, axis=1)
        result = pd.concat([df.reset_index(drop=True), scaled_df[['GSS', 'Diagnosis']]], axis=1)
        return result

    except Exception as e:
        st.error("❌ Error during GSS calculation:")
        st.error(traceback.format_exc())
        return pd.DataFrame()

# ========== Streamlit App ==========
def main():
    st.set_page_config(page_title="Grazing Suitability Checker", layout="wide")
    st.title("🌾 Grazing Suitability Score (GSS) Calculator with AI Suggestions")
    st.sidebar.header("Upload Your Data")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.success("✅ File uploaded successfully.")
        except Exception as e:
            st.error(f"❌ Failed to read file: {e}")
            return

        required_cols = ['Plot Name', 'available_biomass', 'Shrub %', 'grazing_pressure', 'total woody count']
        if not set(required_cols).issubset(df.columns):
            missing = set(required_cols) - set(df.columns)
            st.error(f"❌ Missing columns: {missing}")
            return

        if df[required_cols].isnull().any().any():
            st.error("❌ Your file contains missing values in required columns. Please clean the data and try again.")
            return

        with st.spinner("🧠 Calculating GSS and generating suggestions..."):
            result = calculate_gss(df)

        if result.empty:
            return

        st.subheader("📋 First 5 rows of your data:")
        st.dataframe(result.head())

        # Download Option
        download_option = st.selectbox(
            "Choose result type for download:",
            ("Full Data (All Columns)", "Minimal (Plot Name & GSS Only)")
        )

        if download_option == "Full Data (All Columns)":
            output_df = result.copy()
        else:
            output_df = result[['Plot Name', 'GSS']]

        csv = output_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download results as CSV",
            data=csv,
            file_name='gss_results_filtered.csv',
            mime='text/csv'
        )

        # Recommendation per Plot
        st.sidebar.markdown("---")
        st.sidebar.header("🧠 AI Recommendation")
        language = st.sidebar.selectbox("Choose Language", ["English", "Hausa"])
        selected_plot = st.sidebar.selectbox("Select Plot", result['Plot Name'].unique())

        selected_row = result[result['Plot Name'] == selected_plot].iloc[0]
        score = selected_row['GSS']
        recommendation = get_recommendation(score, language)

        st.sidebar.markdown(f"**AI Suggestion:** {recommendation}")

        if st.sidebar.button("🔊 Play Voice"):
            play_voice(score, language)

        st.subheader("📈 Grazing Suitability Score Distribution")
        st.bar_chart(result['GSS'])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Top 5 Plots")
            st.dataframe(result.sort_values('GSS', ascending=False).head(5))
        with col2:
            st.markdown("#### Bottom 5 Plots")
            st.dataframe(result.sort_values('GSS', ascending=True).head(5))

    else:
        st.info("📂 Upload a CSV or Excel file to begin.")
        st.markdown("Required columns: `Plot Name`, `available_biomass`, `Shrub %`, `grazing_pressure`, `total woody count`.")

if __name__ == "__main__":
    main()
