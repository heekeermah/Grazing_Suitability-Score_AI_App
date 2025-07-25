# Grazing_Suitability_Score_AI_App
#Welcome! This is my AI-based Grazing Suitability Score app, built to support rangeland management with smart, local insights.

This was built with python, streamlit, OpenAI, and gTTS.

#User Manual
once you upload your data through the sidebar, the app extracts key indicators - like biomass, shrub percentage, grazing pressure, and total woody plants - and rescales them using the Min-Max  Scaler.
it then calculates a grazing suitability score for each plot and provides a short diagonis
users can select any plot and get an instant recommendation - either a rule based response or a smarter one fron OpenAI's GPT in English or Hausa
for data analysts, the app displays the first rows, scaled values, full results - and lets you download either the complete dataset or just the plot names and GSS
if your data contains latitude and longitude and longitude, the app plots it on a map.
