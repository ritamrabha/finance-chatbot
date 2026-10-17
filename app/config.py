"""Central configuration. Every setting comes from environment variables
(or a local .env file), so no secret ever lives in the code.

Each Azure service is optional: if its settings are blank, the app falls back
to a local equivalent (SQLite, local folder, demo extractor). That lets the
app run on a laptop with zero cloud setup, and switch to Azure by only
changing settings.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _load_from_key_vault() -> None:
    """Optional: pull secrets from Azure Key Vault into the environment.

    Secret names in Key Vault use dashes (LLM-API-KEY); we map them to
    env-var style (LLM_API_KEY). Authentication uses DefaultAzureCredential,
    i.e. the App Service managed identity in the cloud or `az login` locally,
    so there is still no password in code.
    """
    vault_url = os.getenv("KEY_VAULT_URL", "").strip()
    if not vault_url:
        return
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
    for prop in client.list_properties_of_secrets():
        env_name = prop.name.replace("-", "_").upper()
        if not os.getenv(env_name):
            os.environ[env_name] = client.get_secret(prop.name).value or ""


_load_from_key_vault()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    # LLM
    llm_base_url: str = _env("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    llm_model: str = _env("LLM_MODEL", "llama-3.3-70b-versatile")
    llm_api_key: str = _env("LLM_API_KEY")

    # Login
    app_username: str = _env("APP_USERNAME", "admin")
    app_password_hash: str = _env("APP_PASSWORD_HASH")

    # Document Intelligence
    docintel_endpoint: str = _env("AZURE_DOCINTEL_ENDPOINT")
    docintel_key: str = _env("AZURE_DOCINTEL_KEY")

    # Blob Storage
    storage_conn_str: str = _env("AZURE_STORAGE_CONNECTION_STRING")
    storage_container: str = _env("AZURE_STORAGE_CONTAINER", "invoices")

    # Azure SQL
    sql_server: str = _env("AZURE_SQL_SERVER")
    sql_database: str = _env("AZURE_SQL_DATABASE")
    sql_writer_user: str = _env("AZURE_SQL_WRITER_USER")
    sql_writer_password: str = _env("AZURE_SQL_WRITER_PASSWORD")
    sql_reader_user: str = _env("AZURE_SQL_READER_USER")
    sql_reader_password: str = _env("AZURE_SQL_READER_PASSWORD")

    # Monitoring
    appinsights_conn_str: str = _env("APPLICATIONINSIGHTS_CONNECTION_STRING")

    # Local paths
    sqlite_path: Path = ROOT / "data" / "invoices.db"
    local_upload_dir: Path = ROOT / "data" / "uploads"

    # Upload limits
    max_upload_mb: int = 10

    @property
    def use_azure_sql(self) -> bool:
        return bool(self.sql_server and self.sql_database)

    @property
    def use_docintel(self) -> bool:
        return bool(self.docintel_endpoint and self.docintel_key)

    @property
    def use_blob(self) -> bool:
        return bool(self.storage_conn_str)

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_base_url and self.llm_model)


settings = Settings()

# Demo currency conversion so INR and GBP invoices can be compared in one
# number. A real system would use daily FX rates; a fixed rate is enough here.
FX_TO_INR = {"INR": 1.0, "GBP": 110.0}
