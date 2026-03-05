from dataclasses import dataclass

import torch
import torch.nn as nn
from transformers import AutoModel


@dataclass
class LayoutModelOutput:
    sequence_output: torch.Tensor
    pooled_output: torch.Tensor


class LayoutAwareEncoder(nn.Module):
    """LayoutLMv3-inspired encoder using textual backbone + learned spatial features."""

    def __init__(self, model_name: str = "distilbert-base-uncased", spatial_dim: int = 64):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        hidden = self.backbone.config.hidden_size
        self.spatial_proj = nn.Sequential(
            nn.Linear(4, spatial_dim),
            nn.ReLU(),
            nn.Linear(spatial_dim, hidden),
        )
        self.section_embed = nn.Embedding(8, hidden)
        self.layer_norm = nn.LayerNorm(hidden)

    def forward(self, input_ids, attention_mask, bbox, section_ids):
        x = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        text_out = x.last_hidden_state
        spatial = self.spatial_proj(bbox.float())
        section = self.section_embed(section_ids)
        fused = self.layer_norm(text_out + spatial + section)
        pooled = fused[:, 0]
        return LayoutModelOutput(sequence_output=fused, pooled_output=pooled)
