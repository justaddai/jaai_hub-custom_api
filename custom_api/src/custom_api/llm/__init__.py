import os
from abc import abstractmethod
from typing import Self

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.utils import convert_to_secret_str
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pydantic import BaseModel, SecretStr

load_dotenv()


class LLMConfig(BaseModel):
    name: str
    model_provider: str | None = None
    model_id: str
    api_version: str | None = None
    max_completion_tokens: int | None = None
    temperature: float = 0.0
    timeout: int = 3000


class LLMBase:
    _instance: Self | None = None

    @classmethod
    def get_instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_client(
        self,
        model_config: LLMConfig,
        seed: int | None = 1397,
    ) -> AzureChatOpenAI | ChatOpenAI:

        llm_api_base: str | None = model_config.model_provider
        llm_api_key: SecretStr = convert_to_secret_str(os.getenv("OPENAI_API_KEY", ""))
        if llm_api_base and "openai.azure.com" in llm_api_base:
            return AzureChatOpenAI(
                name=model_config.name,
                model=model_config.model_id,
                azure_endpoint=llm_api_base,
                api_key=llm_api_key,
                api_version=model_config.api_version or "2024-02-15-preview",
                max_tokens=model_config.max_completion_tokens,
                temperature=model_config.temperature,
                timeout=model_config.timeout,
            )
        else:
            return ChatOpenAI(
                name=model_config.name,
                model=model_config.model_id,
                base_url=llm_api_base,
                api_key=llm_api_key,
                temperature=model_config.temperature,
                timeout=model_config.timeout,
            )

    @abstractmethod
    def get_prompt(self) -> PromptTemplate:
        pass

    @abstractmethod
    async def predict(self, *args, **kwargs) -> BaseModel:
        ...
