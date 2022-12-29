---
layout: post
title: "Correcting Outerra's Logarithmic Depth Buffering"
---

[Outerra has a vertex shader implementation of logarithmic depth in GLSL][1]. However, Outerra missed a major part of their implementation. This is our corrected version of Outerra's logarithmic depth in HLSL.

## Source Code

Outerra missed the extra multiply in the end. We have to multiply log depth by `W` because the GPU automatically divides the vertex position `HPos` by `W`.

```c
// Output.HPos is the computed vertex position in homogeneous space
const float FarPlane = 10000;
const float FCoef = 1.0 / log2(FarPlane + 1.0);
Output.HPos.z = log2(max(1e-6, Output.HPos.w)) * FCoef;
Output.HPos.z *= Output.HPos.w;
```

[1]: https://outerra.blogspot.com/2013/07/logarithmic-depth-buffer-optimizations.html
