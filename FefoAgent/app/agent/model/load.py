import config
from strands.models.bedrock import BedrockModel


def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials. Model_ID config'den okunur ('global.' önekli)."""
    return BedrockModel(model_id=config.get_model_id())
