from pathlib import Path
import yaml

from etl.common.fetch import fetch_and_save


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config" / "sources.yaml"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "jcm_mn"


def load_config() -> dict:
    """
    Load source configuration from config/sources.yaml.
    """
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_jcm_mn_pages() -> list[Path]:
    """
    Fetch the core JCM Mongolia-Japan pages and save them as raw HTML.
    """
    config = load_config()
    pages = config["jcm_mn"]["pages"]

    saved_paths = []

    for page_name, page_info in pages.items():
        url = page_info["url"]
        raw_filename = page_info["raw_filename"]
        output_path = RAW_DIR / raw_filename

        print(f"Fetching {page_name}: {url}")
        saved_path = fetch_and_save(url, output_path)
        print(f"Saved to: {saved_path}")

        saved_paths.append(saved_path)

    return saved_paths


if __name__ == "__main__":
    fetch_jcm_mn_pages()