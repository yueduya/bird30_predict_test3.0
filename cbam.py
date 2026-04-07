import torch
import torch.nn as nn
from torchvision import models


# -------------------- CBAM模块定义 --------------------
class CBAMBlock(nn.Module):
    def __init__(self, channel, reduction=16, kernel_size=7):
        super(CBAMBlock, self).__init__()
        # 通道注意力
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel)
        )
        self.sigmoid = nn.Sigmoid()

        # 空间注意力
        self.conv = nn.Conv2d(2, 1, kernel_size=kernel_size,
                              padding=kernel_size // 2, bias=False)

    def forward(self, x):
        # 通道注意力
        b, c, _, _ = x.size()
        avg_out = self.fc(self.avg_pool(x).view(b, c)).view(b, c, 1, 1)
        max_out = self.fc(self.max_pool(x).view(b, c)).view(b, c, 1, 1)
        channel_out = self.sigmoid(avg_out + max_out)
        x = x * channel_out.expand_as(x)

        # 空间注意力
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        spatial_out = self.sigmoid(self.conv(torch.cat([avg_out, max_out], dim=1)))
        return x * spatial_out


# -------------------- 自定义CBAM BasicBlock --------------------
class CBAMBasicBlock(models.resnet.BasicBlock):
    def __init__(self, inplanes, planes, stride=1, downsample=None,
                 groups=1, base_width=64, dilation=1, norm_layer=None):
        super().__init__(
            inplanes, planes, stride, downsample,
            groups, base_width, dilation, norm_layer
        )
        self.cbam = CBAMBlock(self.conv2.out_channels)

    def forward(self, x):
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        # 插入CBAM
        out = self.cbam(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.relu(out)
        return out


# -------------------- Block替换函数 --------------------
def create_cbam_basicblock(original_block):
    # 提取原始块参数（BasicBlock没有groups/base_width/dilation参数）
    params = {
        'inplanes': original_block.conv1.in_channels,
        'planes': original_block.conv1.out_channels,
        'stride': original_block.stride,
        'downsample': original_block.downsample,
        'norm_layer': type(original_block.bn1)
    }

    # 创建新的CBAM块
    new_block = CBAMBasicBlock(**params)

    # 复制原始块参数
    new_block.conv1.load_state_dict(original_block.conv1.state_dict())
    new_block.bn1.load_state_dict(original_block.bn1.state_dict())
    new_block.conv2.load_state_dict(original_block.conv2.state_dict())
    new_block.bn2.load_state_dict(original_block.bn2.state_dict())

    return new_block


# -------------------- 模型构建函数 --------------------
def build_cbam_resnet18(n_class=30):
    # 加载预训练模型
    model = models.resnet18(pretrained=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 替换所有BasicBlock
    for layer_name in ['layer1', 'layer2', 'layer3', 'layer4']:
        layer = getattr(model, layer_name)
        new_blocks = []
        for original_block in layer:
            new_block = create_cbam_basicblock(original_block)
            new_block = new_block.to(device)
            new_blocks.append(new_block)
        setattr(model, layer_name, nn.Sequential(*new_blocks).to(device))

    # 修改分类头
    model.fc = nn.Linear(model.fc.in_features, n_class).to(device)
    return model.to(device)




