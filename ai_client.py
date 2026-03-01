import openai
import logging
from config import NVIDIA_API_KEYS, NVIDIA_BASE_URL, NVIDIA_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_key_index = 0


def _get_client():
    """Get OpenAI client with NVIDIA NIM endpoint, rotate keys on failure."""
    global _key_index
    key = NVIDIA_API_KEYS[_key_index % len(NVIDIA_API_KEYS)]
    return openai.OpenAI(base_url=NVIDIA_BASE_URL, api_key=key)


def generate_post(product_info: str, referral_link: str) -> str:
    """
    Generate a viral Telegram post using NVIDIA NIM AI.
    Tries all 4 API keys on failure.
    """
    global _key_index

    prompt = f"""Создай вирусный пост для Telegram-канала о гаджетах.

Информация о товаре:
{product_info}

Партнёрская ссылка: {referral_link}

Требования:
- Следуй формату из системного промта строго
- Добавь эмодзи для привлечения внимания
- В конце ОБЯЗАТЕЛЬНО добавь ссылку: {referral_link}
- Длина: 200-400 слов
- Язык: украинский или русский"""

    for attempt in range(len(NVIDIA_API_KEYS)):
        try:
            client = _get_client()
            response = client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=1024,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"AI key {_key_index % len(NVIDIA_API_KEYS)} failed: {e}")
            _key_index += 1

    raise RuntimeError("Все AI ключи недоступны. Попробуй позже.")


def generate_caption_only(product_name: str, referral_link: str, extra: str = "") -> str:
    """Generate short caption for photo posts."""
    global _key_index

    prompt = f"""Напиши короткий вирусный caption для фото-поста в Telegram.
Товар: {product_name}
{f'Доп. инфо: {extra}' if extra else ''}
Ссылка: {referral_link}

Формат: emoji + 3-5 предложений + ссылка + хэштеги. Не более 800 символов."""

    for attempt in range(len(NVIDIA_API_KEYS)):
        try:
            client = _get_client()
            response = client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=512,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"AI key {_key_index % len(NVIDIA_API_KEYS)} failed: {e}")
            _key_index += 1

    raise RuntimeError("Все AI ключи недоступны.")
