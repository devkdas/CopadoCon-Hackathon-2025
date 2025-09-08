"""
Configuration management for our hackathon project
This file handles all the environment variables and settings that make our app work.
Think of it as the central control panel for everything configurable.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    All the settings our application needs to run properly.
    These come from environment variables, with sensible defaults when possible.
    """
    
    # Basic app settings - how and where the server runs
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PORT: int = int(os.getenv("PORT", "8080"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # How often our monitoring agent checks for new problems (in seconds)
    MONITORING_INTERVAL: int = int(os.getenv("MONITORING_INTERVAL", "30"))
    
    # Salesforce connection details - where we monitor for issues
    SALESFORCE_USERNAME: Optional[str] = os.getenv("SALESFORCE_USERNAME")
    SALESFORCE_PASSWORD: Optional[str] = os.getenv("SALESFORCE_PASSWORD")
    SALESFORCE_SECURITY_TOKEN: Optional[str] = os.getenv("SALESFORCE_SECURITY_TOKEN")
    SALESFORCE_DOMAIN: Optional[str] = os.getenv("SALESFORCE_DOMAIN")
    
    # AI services that power our intelligent analysis
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    COPADO_AI_API_KEY: Optional[str] = os.getenv("COPADO_AI_API_KEY")
    
    # GitHub integration for code-related incident tracking
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    GITHUB_WEBHOOK_SECRET: Optional[str] = os.getenv("GITHUB_WEBHOOK_SECRET")
    
    # Jira integration for creating and managing tickets
    JIRA_SERVER: Optional[str] = os.getenv("JIRA_SERVER")
    JIRA_USERNAME: Optional[str] = os.getenv("JIRA_USERNAME")
    JIRA_API_TOKEN: Optional[str] = os.getenv("JIRA_API_TOKEN")
    
    # Slack integration for team notifications and alerts
    SLACK_BOT_TOKEN: Optional[str] = os.getenv("SLACK_BOT_TOKEN")
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    
    # Where we store our data and cache information
    DATABASE_URL: str = "sqlite:///./observability.db"
    REDIS_URL: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"

settings = Settings()
