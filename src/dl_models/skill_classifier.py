import torch
import torch.nn as nn

from src.dl_models.layout_model import LayoutAwareEncoder

try:
    from torchcrf import CRF
except Exception:  # optional dependency fallback
    CRF = None


class SkillExtractModel(nn.Module):
    def __init__(self, base_model: str = "distilbert-base-uncased", num_tags: int = 3, num_sections: int = 6):
        super().__init__()
        self.encoder = LayoutAwareEncoder(base_model)
        hidden = self.encoder.backbone.config.hidden_size
        self.tag_head = nn.Linear(hidden, num_tags)
        self.section_head = nn.Linear(hidden, num_sections)
        self.use_crf = CRF is not None
        self.crf = CRF(num_tags, batch_first=True) if self.use_crf else None

    def forward(self, input_ids, attention_mask, bbox, section_ids, labels=None, section_labels=None):
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask, bbox=bbox, section_ids=section_ids)
        emissions = self.tag_head(out.sequence_output)
        section_logits = self.section_head(out.pooled_output)

        loss = None
        if labels is not None and section_labels is not None:
            section_loss = nn.CrossEntropyLoss()(section_logits, section_labels)
            if self.use_crf:
                token_loss = -self.crf(emissions, labels, mask=attention_mask.bool(), reduction="mean")
            else:
                token_loss = nn.CrossEntropyLoss()(emissions.view(-1, emissions.size(-1)), labels.view(-1))
            loss = token_loss + section_loss

        if self.use_crf:
            pred_tags = self.crf.decode(emissions, mask=attention_mask.bool())
        else:
            pred_tags = emissions.argmax(-1)

        return {
            "loss": loss,
            "emissions": emissions,
            "token_predictions": pred_tags,
            "section_logits": section_logits,
        }
