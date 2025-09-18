import streamlit as st
from kafka import KafkaConsumer
import json
import pandas as pd
import time
import altair as alt
from datetime import datetime

# Налаштування сторінки
st.set_page_config(page_title="Security Event Dashboard", layout="wide")
st.title("📊 Security Events — Візуалізація подій з Kafka")

# Підключення до Kafka
consumer = KafkaConsumer(
    'security-events',  # заміни на свій топік, якщо потрібно
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest',
    enable_auto_commit=True,
    group_id='streamlit-security-dashboard'
)

# Буфер подій
event_buffer = []

chart_placeholder = st.empty()
table_placeholder = st.empty()

while True:
    new_messages = []
    for tp, records in consumer.poll(timeout_ms=1000).items():
        for record in records:
            try:
                event = record.value
                # Переконаймось, що є timestamp
                if "timestamp" not in event:
                    event["timestamp"] = datetime.utcnow().isoformat()
                new_messages.append(event)
            except Exception as e:
                st.error(f"⚠️ Error reading message: {e}")

    # Оновити буфер
    event_buffer.extend(new_messages)
    event_buffer = event_buffer[-300:]  # останні 300 подій

    if event_buffer:
        df = pd.DataFrame(event_buffer)

        # Конвертуємо час
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        df = df.dropna(subset=["timestamp"])

        # ==== Барчарт по event_type ====
        with chart_placeholder.container():
            st.subheader("🎯 Події за типами")

            event_counts = df["event_type"].value_counts().reset_index()
            event_counts.columns = ["event_type", "count"]

            chart = alt.Chart(event_counts).mark_bar().encode(
                x=alt.X("count:Q", title="Кількість"),
                y=alt.Y("event_type:N", sort='-x', title="Тип події"),
                color=alt.Color("event_type:N", legend=None)
            ).properties(width=700, height=400)

            st.altair_chart(chart, use_container_width=True)

        # ==== Таблиця метрик ====
        with table_placeholder.container():
            st.subheader("📋 Повні дані з Kafka")
            st.dataframe(df.sort_values(by="timestamp", ascending=False).reset_index(drop=True))

    time.sleep(2)
