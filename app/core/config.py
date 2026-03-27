from pathlib import Path  
from functools import lru_cache  
from typing import Optional  
from pydantic import Field  
from pydantic_settings import BaseSettings, SettingsConfigDict  
  
PROJECT_ROOT = Path(__file__).resolve().parents[2]  
  
class Settings(BaseSettings):  
    model_config = SettingsConfigDict(env_file=str(PROJECT_ROOT / '.env'), env_file_encoding='utf-8', extra='ignore')  
    app_name: str = Field(default='smart-shopping-agent', alias='APP_NAME')  
    env: str = Field(default='dev', alias='ENV')  
    debug: bool = Field(default=False, alias='DEBUG')  
    api_v1_prefix: str = Field(default='/api/v1', alias='API_V1_PREFIX')  
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')  
    mysql_host: str = Field(default='127.0.0.1', alias='MYSQL_HOST')  
    mysql_port: int = Field(default=3306, alias='MYSQL_PORT')  
    mysql_user: str = Field(default='root', alias='MYSQL_USER')  
    mysql_password: str = Field(default='password', alias='MYSQL_PASSWORD')  
    mysql_db: str = Field(default='smart_shopping_agent', alias='MYSQL_DB')  
    mysql_charset: str = Field(default='utf8mb4', alias='MYSQL_CHARSET')  
    redis_url: str = Field(default='redis://localhost:6379/0', alias='REDIS_URL')  
    llm_provider: str = Field(default='deepseek', alias='LLM_PROVIDER')  
    llm_base_url: Optional[str] = Field(default=None, alias='LLM_BASE_URL')  
    llm_api_key: Optional[str] = Field(default=None, alias='LLM_API_KEY')  
    llm_model: str = Field(default='deepseek-chat', alias='LLM_MODEL')  
    openai_api_key: Optional[str] = Field(default=None, alias='OPENAI_API_KEY')  
    openai_base_url: Optional[str] = Field(default='https://api.deepseek.com', alias='OPENAI_BASE_URL')  
    openai_model: str = Field(default='deepseek-chat', alias='OPENAI_MODEL')  
    max_agent_steps: int = Field(default=6, alias='MAX_AGENT_STEPS')  
  
    @property  
    def database_url(self):  
        return f'mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset={self.mysql_charset}'  
  
    @property  
    def effective_llm_base_url(self):  
        return self.llm_base_url or self.openai_base_url or 'https://api.deepseek.com'  
  
    @property  
    def effective_llm_api_key(self):  
        return self.llm_api_key or self.openai_api_key  
  
    @property  
    def effective_llm_model(self):  
        return self.llm_model or self.openai_model  
  
@lru_cache(maxsize=1)  
def get_settings():  
    return Settings()  
  
settings = get_settings()  
