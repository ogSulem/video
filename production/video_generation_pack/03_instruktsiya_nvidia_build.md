# Инструкция: генерация 4 клипов на NVIDIA (build.nvidia.com)

**Почему не могу сам:** из моей песочницы доступ в интернет ограничен списком домена
(GitHub, PyPI). Проверено прямым обращением:

```
integrate.api.nvidia.com -> TLS handshake заблокирован (SSL_ERROR_SYSCALL)
build.nvidia.com         -> заблокирован
pypi.org                 -> 200 OK  (контроль)
```

Поэтому я подготовил всё, кроме самого вызова. Вызов делаете вы — одной командой.
Ключ остаётся у вас, в чат его присылать не нужно.

---

## Шаг 0. Ключ

```bash
export NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxx
```

Никогда не записывайте ключ в файлы репозитория.

## Шаг 1. Узнать, какие видеомодели видит ваш ключ

```bash
python video/nvidia_i2v.py --list-models
```

Скрипт отметит звёздочкой всё, что похоже на видео (video / i2v / wan / cosmos /
ltx / svd). Имена моделей у NVIDIA меняются, поэтому шаг обязателен —
дальше подставляется найденный id.

## Шаг 2. Проверить запрос без отправки

```bash
python video/nvidia_i2v.py --clip A --model <MODEL_ID> --dry-run
```

Покажет промпт, картинку-референс, длительность, разрешение — ничего не отправит.

## Шаг 3. Сгенерировать

```bash
python video/nvidia_i2v.py --clip A --model <MODEL_ID>
python video/nvidia_i2v.py --clip B --model <MODEL_ID>
python video/nvidia_i2v.py --clip C --model <MODEL_ID>
python video/nvidia_i2v.py --clip D --model <MODEL_ID>
# или сразу все четыре:
python video/nvidia_i2v.py --all --model <MODEL_ID> --duration 10
```

Файлы появятся здесь:

```
video/shots/ai_hero_clips/clipA.mp4
video/shots/ai_hero_clips/clipB.mp4
video/shots/ai_hero_clips/clipC.mp4
video/shots/ai_hero_clips/clipD.mp4
```

## Шаг 4. Собрать фильм

```bash
.venv/bin/python video/tools/assemble_hero_clips.py --force
```

→ `video/final/altai_rehabilitation_hero_v1.mp4` — 77 секунд, 1920×1080, 24 fps,
одобренная озвучка уже внутри.

---

## Если сервер ответил ошибкой

Скрипт печатает ответ сервера целиком. Пришлите этот текст в чат — я поправлю
вызов под фактическую схему API (сейчас поддержаны три: `--shape json_b64`,
`--shape multipart`, `--shape json_seedance`, плюс асинхронный опрос NVCF).

Частые случаи:

| Ответ | Что делать |
|---|---|
| `404 model not found` | уточнить id через `--list-models` |
| `422 / 400 invalid payload` | сменить `--shape`, чаще всего на `multipart` |
| `payload too large` | референс больше лимита: уменьшить PNG до 1280×720 |
| `unsupported size` | попробовать `--size 1280x720` (скрипт сборки всё равно приведёт к 1920×1080) |
| `403 forbidden` | модель не входит в тариф ключа, взять другую из списка |

## Если модель не принимает картинку (только текст)

Это не блокер: промпты уже содержат полное описание героя — строку
«The man is about 32 years old…» из `02_promty_dlya_battle_mode.md`.
Можно сгенерировать text-to-video, но совпадение лица будет хуже. В таком случае
лучше сначала сгенерировать кадр-ключ по референсу (как мы уже делали для
`kf01…kf05`), а затем подать его как первый кадр видео.

## Если лимит «4 видео» относится к battle mode, а не к NVIDIA

Тогда выберите один из двух маршрутов — они не конфликтуют:

- **NVIDIA** — столько клипов, сколько даёт ключ; результат кладётся в те же
  `video/shots/ai_hero_clips/`.
- **Battle mode** — ровно 4 генерации, промпты и картинки берите из
  `04_kak_peredat_v_battle_mode.md`.

Оба маршрута скармливаются одному и тому же сборщику.
