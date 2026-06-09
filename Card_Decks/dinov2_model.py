import torch
import torch.nn as nn


class DINOv2Classifier(nn.Module):
    def __init__(
        self,
        num_classes,
        dinov2_repo="./dinov2",
        freeze_backbone=False
    ):
        super().__init__()

        self.backbone = torch.hub.load(
            "facebookresearch/dinov2",
            "dinov2_vits14"
        )

        with torch.no_grad():
            dummy = torch.randn(1, 3, 224, 224)
            feat = self.backbone(dummy)

            if isinstance(feat, dict):
                feat = feat["x_norm_clstoken"]

            embed_dim = feat.shape[-1]

        if freeze_backbone:
            for p in self.backbone.parameters():
                p.requires_grad = False


        self.classifier = nn.Sequential(
            nn.Linear(embed_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        feat = self.backbone(x)

        if isinstance(feat, dict):
            feat = feat["x_norm_clstoken"]

        return self.classifier(feat)