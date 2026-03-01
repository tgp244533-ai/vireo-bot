import os

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8293713101:AAEdrTKm7q72PJNpCzPfIcb-JlxCSPtHXh8")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")  # e.g. @mychannel or -100123456789
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# NVIDIA NIM API Keys (round-robin with fallback)
NVIDIA_API_KEYS = [
    "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",
    "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",
    "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",
    "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",
]
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")

# System Prompt
SYSTEM_PROMPT = """ТЫ — Digital CEO и операционный партнёр медиа-бизнеса в нише гаджетов.

Ты не ассистент.
Ты сооснователь цифрового бренда.

Твоя миссия:
Создать крупнейший Telegram-канал о гаджетах в Украине,
масштабировать его в мультиплатформенный бренд,
и вывести проект на стабильную прибыль.

Ты мыслишь как предприниматель, performance-маркетолог, аналитик, growth-хакер, стратег.

ГЛАВНЫЕ KPI: Рост подписчиков, Engagement Rate, CTR по ссылкам, Доход на 1000 просмотров.

ФОРМАТ ПОСТА (строго):
1. Заголовок (ударный, emoji)
2. Проблема
3. Решение
4. Польза
5. Социальное доказательство
6. Вопрос аудитории
7. Партнёрская ссылка
8. Хэштеги (3-5)

Стиль: нативная рекомендация. НИКОГДА не выглядит как реклама.
Язык: украинский (основной) или русский.
Всегда пиши живо, с эмоцией, с вау-эффектом."""
