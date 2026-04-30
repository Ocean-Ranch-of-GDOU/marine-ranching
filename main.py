import logging
import os
import platform
import subprocess
import threading
import time
import urllib.request
import webbrowser

from app.main import app


HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8080"))
BROWSER_HOST = os.getenv("BROWSER_HOST", "127.0.0.1")
AUTO_OPEN_BROWSER = os.getenv("AUTO_OPEN_BROWSER", "1").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}
AUTO_OPEN_DOCS = os.getenv("AUTO_OPEN_DOCS", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def _is_wsl() -> bool:
    try:
        version = platform.release().lower()
        with open("/proc/version", encoding="utf-8") as version_file:
            version += version_file.read().lower()
        return "microsoft" in version or "wsl" in version
    except OSError:
        return False


def _open_url(url: str) -> None:
    if _is_wsl():
        for command in (
            ["wslview", url],
            ["cmd.exe", "/c", "start", "", url],
            ["powershell.exe", "-NoProfile", "-Command", "Start-Process", url],
        ):
            try:
                result = subprocess.run(
                    command,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if result.returncode == 0:
                    return
            except OSError:
                continue
        return

    webbrowser.open_new_tab(url)


def _open_pages_when_ready(port: int) -> None:
    base_url = f"http://{BROWSER_HOST}:{port}"
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{base_url}/", timeout=1).close()
            break
        except OSError:
            time.sleep(0.5)
    else:
        return

    _open_url(f"{base_url}/")
    if AUTO_OPEN_DOCS:
        _open_url(f"{base_url}/docs")


def _print_startup_urls(port: int) -> None:
    base_url = f"http://{BROWSER_HOST}:{port}"
    print()
    print(f"Service listening on: http://{HOST}:{port}", flush=True)
    print(f"Frontend page:       {base_url}/", flush=True)
    print(f"Backend docs page:   {base_url}/docs", flush=True)
    print(f"Frontend auto-open:  {'enabled' if AUTO_OPEN_BROWSER else 'disabled'}", flush=True)
    print(f"Docs auto-open:      {'enabled' if AUTO_OPEN_DOCS else 'disabled'}", flush=True)
    print()


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    _print_startup_urls(PORT)

    if AUTO_OPEN_BROWSER:
        threading.Thread(
            target=_open_pages_when_ready,
            args=(PORT,),
            daemon=True,
        ).start()

    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
