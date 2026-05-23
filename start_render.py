import uvicorn

from web import app


def main() -> None:
    """
    Запускает FastAPI backend для Mini App и Telegram webhook на порту Waifly.
    """

    port = 28015

    print(f"Finvichik web backend запускается на порту {port}...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()