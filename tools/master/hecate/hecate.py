"""Standalone Hecate inference; architecture derived from scrollprize/villa's
canonical ResNet-152 3D decoder and CanonicalLogitProjection.
Only the two released Hecate EMA architectures are supported.
"""
import argparse
import json
from pathlib import Path
import tempfile
import struct
import zlib

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F


def conv3x3x3(in_planes, out_planes, stride=1):
    return nn.Conv3d(in_planes, out_planes, kernel_size=3, stride=stride, padding=1, bias=False)


def conv1x1x1(in_planes, out_planes, stride=1):
    return nn.Conv3d(in_planes, out_planes, kernel_size=1, stride=stride, bias=False)


class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, in_planes, planes, stride=1, downsample=None):
        super().__init__()
        self.conv1 = conv1x1x1(in_planes, planes)
        self.bn1 = nn.BatchNorm3d(planes)
        self.conv2 = conv3x3x3(planes, planes, stride)
        self.bn2 = nn.BatchNorm3d(planes)
        self.conv3 = conv1x1x1(planes, planes * self.expansion)
        self.bn3 = nn.BatchNorm3d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out


class ResNet(nn.Module):

    def __init__(self, block, layers, block_inplanes, n_input_channels=3, conv1_t_size=7, conv1_t_stride=1, no_max_pool=False, shortcut_type='B', widen_factor=1.0, n_classes=400, forward_features=False):
        super().__init__()
        self.forward_features = forward_features
        block_inplanes = [int(x * widen_factor) for x in block_inplanes]
        self.in_planes = block_inplanes[0]
        self.no_max_pool = no_max_pool
        self.conv1 = nn.Conv3d(n_input_channels, self.in_planes, kernel_size=(conv1_t_size, 7, 7), stride=(conv1_t_stride, 2, 2), padding=(conv1_t_size // 2, 3, 3), bias=False)
        self.bn1 = nn.BatchNorm3d(self.in_planes)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1))
        self.layer1 = self._make_layer(block, block_inplanes[0], layers[0], shortcut_type)
        self.layer2 = self._make_layer(block, block_inplanes[1], layers[1], shortcut_type, stride=2)
        self.layer3 = self._make_layer(block, block_inplanes[2], layers[2], shortcut_type, stride=2)
        self.layer4 = self._make_layer(block, block_inplanes[3], layers[3], shortcut_type, stride=2)
        self.avgpool = nn.AdaptiveMaxPool3d((1, 1, 1))
        self.fc = nn.Linear(block_inplanes[3] * block.expansion, n_classes)
        for m in self.modules():
            if isinstance(m, nn.Conv3d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm3d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def _make_layer(self, block, planes, blocks, shortcut_type, stride=1):
        downsample = None
        if stride != 1 or self.in_planes != planes * block.expansion:
            if False:
                raise ValueError('Only shortcut B is supported')
            else:
                downsample = nn.Sequential(conv1x1x1(self.in_planes, planes * block.expansion, stride), nn.BatchNorm3d(planes * block.expansion))
        layers = []
        layers.append(block(in_planes=self.in_planes, planes=planes, stride=stride, downsample=downsample))
        self.in_planes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.in_planes, planes))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        if not self.no_max_pool:
            x = self.maxpool(x)
        x1 = self.layer1(x)
        x2 = self.layer2(x1)
        x3 = self.layer3(x2)
        x4 = self.layer4(x3)
        if self.forward_features:
            return [x1, x2, x3, x4]
        else:
            x = self.avgpool(x4)
            x = x.view(x.size(0), -1)
            x = self.fc(x)
            return x


class ResConvBlock3D(nn.Module):

    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv1 = nn.Conv3d(in_ch, out_ch, 3, padding=1, bias=False)
        self.gn1 = nn.GroupNorm(min(32, out_ch), out_ch)
        self.conv2 = nn.Conv3d(out_ch, out_ch, 3, padding=1, bias=False)
        self.gn2 = nn.GroupNorm(min(32, out_ch), out_ch)
        self.shortcut = nn.Conv3d(in_ch, out_ch, 1, bias=False) if in_ch != out_ch else nn.Identity()

    def forward(self, x):
        identity = self.shortcut(x)
        x = F.relu(self.gn1(self.conv1(x)), inplace=True)
        x = self.gn2(self.conv2(x))
        x = F.relu(x + identity, inplace=True)
        return x


class DepthAttentionCollapse(nn.Module):

    def __init__(self, in_ch):
        super().__init__()
        self.attn_conv = nn.Conv3d(in_ch, 1, 1)


class AuxHead(nn.Module):

    def __init__(self, in_ch, target_size=64):
        super().__init__()
        self.pool = nn.AdaptiveAvgPool3d((1, None, None))
        self.conv = nn.Conv2d(in_ch, 1, 1)
        self.target_size = target_size


class Decoder3DUNet(nn.Module):

    def __init__(self, encoder_dims=(256, 512, 1024, 2048), decoder_dims=(64, 128, 256, 512), deep_supervision=True):
        super().__init__()
        self.deep_supervision = deep_supervision
        self.channel_reduce = nn.ModuleList([nn.Sequential(nn.Conv3d(enc_d, dec_d, 1, bias=False), nn.GroupNorm(min(32, dec_d), dec_d), nn.ReLU(inplace=True)) for enc_d, dec_d in zip(encoder_dims, decoder_dims)])
        self.decoder_blocks = nn.ModuleList([ResConvBlock3D(decoder_dims[i] + decoder_dims[i - 1], decoder_dims[i - 1]) for i in range(len(decoder_dims) - 1, 0, -1)])
        self.depth_collapse = DepthAttentionCollapse(decoder_dims[0])
        self.logit = nn.Conv2d(decoder_dims[0], 1, 1)
        if deep_supervision:
            self.aux_head_s2 = AuxHead(decoder_dims[2])
            self.aux_head_s1 = AuxHead(decoder_dims[1])

    def forward_features(self, feat_maps):
        """Decode once, retaining the feature volume before depth collapse."""
        feats = [self.channel_reduce[i](feat_maps[i]) for i in range(4)]
        aux_outputs = []
        x = feats[3]
        x = F.interpolate(x, size=feats[2].shape[2:], mode='trilinear', align_corners=False)
        x = torch.cat([x, feats[2]], dim=1)
        x = self.decoder_blocks[0](x)
        if self.deep_supervision and self.training:
            aux_outputs.append(self.aux_head_s2(x))
        x = F.interpolate(x, size=feats[1].shape[2:], mode='trilinear', align_corners=False)
        x = torch.cat([x, feats[1]], dim=1)
        x = self.decoder_blocks[1](x)
        if self.deep_supervision and self.training:
            aux_outputs.append(self.aux_head_s1(x))
        x = F.interpolate(x, size=feats[0].shape[2:], mode='trilinear', align_corners=False)
        x = torch.cat([x, feats[0]], dim=1)
        x = self.decoder_blocks[2](x)
        return (x, aux_outputs)


class RegressionModel(nn.Module):

    def __init__(self, with_norm=False):
        super().__init__()
        self.backbone = ResNet(Bottleneck, [3, 8, 36, 3], [64, 128, 256, 512], n_input_channels=1, forward_features=True, n_classes=1039)
        self.decoder = Decoder3DUNet(encoder_dims=(256, 512, 1024, 2048), decoder_dims=(64, 128, 256, 512), deep_supervision=True)
        self.normalization = nn.BatchNorm3d(num_features=1) if with_norm else None

    def encode(self, x: torch.Tensor):
        if x.ndim == 4:
            x = x[:, None]
        if self.normalization is not None:
            x = self.normalization(x)
        return self.backbone(x)

    def forward_features(self, x: torch.Tensor):
        return self.decoder.forward_features(self.encode(x))


class SpatialMaxPool3d(nn.Module):
    def forward(self, x):
        b, c, d, h, w = x.shape
        out = F.max_pool2d(x.reshape(b*c*d, 1, h, w), 3, 2, 1)
        return out.reshape(b, c, d, *out.shape[-2:])


class Hecate(nn.Module):
    def __init__(self, patch_size, sampling_um):
        super().__init__()
        self.patch_size = tuple(patch_size)
        if (sampling_um, self.patch_size) not in (
                (2.4, (64, 256, 256)), (9.6, (16, 64, 64))):
            raise ValueError('Unsupported Hecate sampling/patch geometry')
        self.sampling_um = sampling_um
        self.margin = 1 if sampling_um == 2.4 else 0
        self.xy_stride = 4 if sampling_um == 2.4 else 1
        self.divisor = 200. if sampling_um == 2.4 else 255.
        self.canonical = RegressionModel(with_norm=True)
        self.canonical.decoder.deep_supervision = False
        self.canonical.backbone.maxpool = SpatialMaxPool3d()
        if self.xy_stride == 1:
            self.canonical.backbone.conv1 = nn.Conv3d(1, 64, 3, padding=1, bias=False)
            self.canonical.backbone.maxpool = nn.Identity()
        self.depth_coordinate_scale = nn.Parameter(torch.zeros(()))

    def features_logits(self, image):
        if tuple(image.shape[1:]) != (1, *self.patch_size):
            raise ValueError(f'Expected B,1,{self.patch_size}, got {tuple(image.shape)}')
        d = self.patch_size[0]
        features, _ = self.canonical.forward_features(image[:, :, self.margin:d-self.margin])
        head = self.canonical.decoder.logit
        logits = F.conv3d(features.float(), head.weight.float().unsqueeze(2), head.bias.float())
        return features, logits.float()

    def forward_3d(self, image):
        """3D logits on the input grid; image is already normalized, B1ZYX.

        This path does not execute attention or the 2D projection.
        The 2.4um model's outermost planes are untrained and padded with -20.
        """
        _, logits = self.features_logits(image)
        full = F.interpolate(logits, size=(self.patch_size[0]-2*self.margin, *image.shape[-2:]),
                             mode='trilinear', align_corners=False)
        return F.pad(full, (0, 0, 0, 0, self.margin, self.margin), value=-20.)

    def forward(self, image, valid=None):
        """2D logits; image is already normalized, B1ZYX; valid is optional B1ZYX."""
        features, logits = self.features_logits(image)
        scores = self.canonical.decoder.depth_collapse.attn_conv(features).float()
        half = scores.shape[2] // 2
        z = (torch.arange(scores.shape[2], device=scores.device, dtype=torch.float32)-half)/half
        scores = scores + self.depth_coordinate_scale*z.view(1, 1, -1, 1, 1)
        if valid is None:
            support = torch.ones_like(logits, dtype=torch.bool)
        else:
            support = F.max_pool3d(valid[:, :, self.margin:self.patch_size[0]-self.margin].float(),
                                   (1, self.xy_stride, self.xy_stride)).bool()
        weights = scores.masked_fill(~support, -1e4).softmax(2)*support
        weights = weights/weights.sum(2, keepdim=True).clamp_min(1e-8)
        probability = F.interpolate((weights*logits).sum(2).sigmoid(), size=image.shape[-2:],
                                    mode='bilinear', align_corners=False)
        eps = torch.finfo(torch.float32).eps
        return torch.logit(probability.clamp(eps, 1-eps))


def load_model(checkpoint, device='cpu'):
    """Strictly load a released inference-only EMA checkpoint."""
    payload = torch.load(checkpoint, map_location='cpu', weights_only=True, mmap=True)
    if payload.get('architecture_family') != 'hecate' or payload.get('weight_source') != 'ema_model':
        raise ValueError('Use a released Hecate inference checkpoint')
    model = Hecate(payload['config']['patch_size'], payload['sampling_um'])
    config = payload['config']
    canonical = config['model_config']['canonical']
    if (config['image_normalization'] != {'mode': 'divide', 'divisor': model.divisor}
            or canonical.get('native_refinement', False)
            or canonical['native_xy_stride'] != model.xy_stride
            or canonical['depth_margin'] != model.margin
            or not canonical['with_norm']):
        raise ValueError('Checkpoint configuration does not match the released architecture')
    model.load_state_dict(payload['ema_model'], strict=True)
    return model.requires_grad_(False).eval().to(device)


def axis_starts(length, patch, stride):
    return list(range(0, max(0, length-patch), stride)) + [max(0, length-patch)]


def open_volume(path, array='0'):
    if str(path).endswith('.npy'):
        volume = np.load(path, mmap_mode='r', allow_pickle=False)
    else:
        import zarr
        volume = zarr.open(str(path), mode='r')
        if not hasattr(volume, 'shape'):
            volume = volume[array]
    if len(volume.shape) != 3 or np.dtype(volume.dtype) != np.dtype('uint8'):
        raise ValueError('Input must be an unnormalized uint8 Z,Y,X surface volume')
    return volume


@torch.inference_mode()
def predict(model, volume, output, reverse=False, stride=None, batch_size=1, precision='fp32', three_d=False):
    """Tiled 2D or 3D uint8 probabilities into a writable HxW array (can be a memmap).

    Reads only individual CT patches. Accumulators use temporary disk-backed
    arrays, so a full surface volume never needs to fit in RAM or GPU memory.
    """
    d, p, _ = model.patch_size
    depth, h, w = volume.shape
    stride = p//2 if stride is None else stride
    if depth < d or not 0 < stride <= p or batch_size < 1:
        raise ValueError('Insufficient depth, invalid stride, or invalid batch size')
    expected_shape = (depth,h,w) if three_d else (h,w)
    if tuple(output.shape) != expected_shape or output.dtype != np.uint8:
        raise ValueError(f'Output must be a uint8 array of shape {expected_shape}')
    if three_d:
        output[:] = 0
    device = next(model.parameters()).device
    if precision not in ('fp32', 'bf16') or (precision == 'bf16' and device.type != 'cuda'):
        raise ValueError('bf16 requires CUDA; otherwise use fp32')
    z0 = depth//2-d//2
    zs = slice(depth-z0-d, depth-z0) if reverse else slice(z0, z0+d)
    win = torch.hann_window(p, periodic=False)
    win = win[:, None]*win[None, :]
    win = (win/win.max().clamp_min(torch.finfo(torch.float32).eps)).clamp_min(.001)
    window = win.numpy()
    win = win.to(device)
    origins = [(y, x) for y in axis_starts(h,p,stride) for x in axis_starts(w,p,stride)]
    with tempfile.TemporaryDirectory(prefix='hecate-') as tmp:
        numerator = np.memmap(Path(tmp)/'sum', mode='w+', dtype='float32', shape=(d,h,w) if three_d else (h,w))
        denominator = np.memmap(Path(tmp)/'weight', mode='w+', dtype='float32', shape=(h,w))
        for start in range(0, len(origins), batch_size):
            active, patches = [], []
            for y, x in origins[start:start+batch_size]:
                ph, pw = min(p,h-y), min(p,w-x)
                denominator[y:y+ph,x:x+pw] += window[:ph,:pw]
                raw = np.asarray(volume[zs,y:y+ph,x:x+pw])
                if reverse:
                    raw = raw[::-1]
                if not raw.any():
                    continue
                patch = np.zeros((d,p,p), dtype=np.uint8)
                patch[:,:ph,:pw] = raw
                patches.append(patch)
                active.append((y,x,ph,pw))
            if patches:
                raw = torch.from_numpy(np.stack(patches)).to(device)
                support = raw.any(1)
                normalized = np.stack(patches).astype(np.float32)
                normalized /= model.divisor  # Match original CPU division; no clipping.
                image = torch.from_numpy(normalized[:,None]).to(device)
                valid = support[:,None,None].expand(-1,1,d,-1,-1)
                with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=precision=='bf16'):
                    logits = model.forward_3d(image) if three_d else model(image, valid)
                    probability = logits.float().sigmoid()[:,0]
                if three_d:
                    support = support[:,None]
                weighted = (probability*support*win).cpu().numpy()
                for pred,(y,x,ph,pw) in zip(weighted,active):
                    numerator[...,y:y+ph,x:x+pw] += pred[..., :ph,:pw]
            if start == 0 or start+batch_size >= len(origins) or start % 100 == 0:
                print(f'{min(start+batch_size,len(origins))}/{len(origins)} patches', flush=True)
        if three_d and model.margin:
            numerator[:model.margin] = 0
            numerator[-model.margin:] = 0
        for y in range(0,h,128):
            for x in range(0,w,256):
                prob = numerator[...,y:y+128,x:x+256]/denominator[y:y+128,x:x+256]
                if not np.isfinite(prob).all():
                    raise FloatingPointError('Non-finite inference output')
                values = np.rint(prob.clip(0,1)*255).astype(np.uint8)
                if three_d:
                    output[zs,y:y+128,x:x+256] = values[::-1] if reverse else values
                else:
                    output[y:y+128,x:x+256] = values
        del numerator, denominator


def write_png(array, path):
    """Losslessly compressed grayscale PNG; streamed to avoid full-image copies."""
    with Path(path).open('wb') as stream:
        def chunk(kind, data):
            stream.write(struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff))
        stream.write(b'\x89PNG\r\n\x1a\n')
        h,w = array.shape
        chunk(b'IHDR',struct.pack('!2I5B',w,h,8,0,0,0,0))
        compressor = zlib.compressobj(9)
        for row in array:
            filtered = row.copy()
            filtered[1:] = row[1:]-row[:-1]
            data = compressor.compress(b'\x01'+filtered.tobytes())
            if data:
                chunk(b'IDAT',data)
        chunk(b'IDAT',compressor.flush())
        chunk(b'IEND',b'')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--input', required=True, help='uint8 ZYX .npy or local Zarr')
    parser.add_argument('--array', default='0', help='Array within a Zarr group')
    parser.add_argument('--output', help='2D probability PNG (optional with --output-3d)')
    parser.add_argument('--output-3d', help='Compressed uint8 3D probability Zarr')
    parser.add_argument('--spacing-um', type=float, required=True, help='Actual isotropic render spacing, not raw scan spacing')
    parser.add_argument('--reverse', action='store_true', help='Reverse full Z before selecting the central input planes')
    parser.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--stride', type=int, help='XY stride; default half the trained patch width')
    parser.add_argument('--precision', choices=('fp32','bf16'), default='fp32')
    args = parser.parse_args()
    if not args.output and not args.output_3d:
        parser.error('Specify --output and/or --output-3d')
    output = Path(args.output) if args.output else None
    output3d = Path(args.output_3d) if args.output_3d else None
    for path,suffix in ((output,'.png'),(output3d,'.zarr')):
        if path is not None and (path.suffix.lower()!=suffix or path.exists()):
            parser.error(f'Choose a new output filename ending in {suffix}: {path}')
    model = load_model(args.checkpoint,args.device)
    if abs(args.spacing_um/model.sampling_um-1) > .02:
        parser.error(f'Resample the render to {model.sampling_um} um first (no automatic resampling)')
    volume = open_volume(args.input,args.array)
    if output is not None:
        output.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='hecate-') as tmp:
            result = np.memmap(Path(tmp)/'prediction',mode='w+',dtype='uint8',shape=volume.shape[-2:])
            predict(model,volume,result,args.reverse,args.stride,args.batch_size,args.precision)
            partial = output.with_suffix('.partial')
            write_png(result,partial)
            partial.replace(output)
            del result
    metadata = {
        'checkpoint':Path(args.checkpoint).name,'sampling_um':args.spacing_um,
        'shape_yx':list(volume.shape[-2:]),'reverse_z':args.reverse,
        'central_depth':model.patch_size[0],'precision':args.precision,
        'stride':args.stride or model.patch_size[1]//2,
        'probabilities':'uint8 = round(255 * probability); no min-max scaling'
    }
    if output is not None:
        output.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print(output)
    if output3d is not None:
        import zarr
        from numcodecs import Blosc
        output3d.parent.mkdir(parents=True,exist_ok=True)
        partial = output3d.with_name(output3d.name+'.partial')
        if partial.exists():
            parser.error(f'Incomplete output exists: {partial}; remove it or choose another output')
        options = {'zarr_format':2} if int(zarr.__version__.split('.')[0])>=3 else {}
        result = zarr.open_array(str(partial),mode='w',shape=volume.shape,
            chunks=(1,256,256),dtype='uint8',fill_value=0,
            compressor=Blosc(cname='zstd',clevel=3,shuffle=Blosc.BITSHUFFLE),**options)
        predict(model,volume,result,args.reverse,args.stride,args.batch_size,args.precision,three_d=True)
        depth = volume.shape[0]
        d = model.patch_size[0]
        start = depth//2-d//2
        if args.reverse:
            start = depth-start-d
        result.attrs.update({**metadata,'axes':['z','y','x'],
            'spacing_um':[args.spacing_um]*3,'z_order':'same as input',
            'evaluated_z_interval':[start+model.margin,start+d-model.margin],
            'outside_evaluated_z':'zero; not evaluated',
            'background':'empty CT columns zeroed; no intensity threshold'})
        partial.rename(output3d)
        print(output3d)



if __name__ == '__main__':
    main()
