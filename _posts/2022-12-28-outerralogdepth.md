---
layout: post
title: "Correcting Outerra's Logarithmic Depth Buffering"
---

[Outerra has a vertex shader implementation of log depth buffering in GLSL][1]. However, Outerra missed a major part of their log depth buffering. This is our corrected version of Outerra's log depth buffering in HLSL.

## Source Code

Outerra missed a multiply in the end. We must multiply log depth by `W` because the GPU automatically divides the vertex position `HPos` by `W`.

```c
// Output.HPos is the computed vertex position in homogeneous space
const float FarPlane = 10000.0;
const float FCoef = 1.0 / log2(FarPlane + 1.0);
Output.HPos.z = saturate(log2(max(1e-6, Output.HPos.w)) * FCoef);
Output.HPos.z *= Output.HPos.w;
```

[1]: https://outerra.blogspot.com/2013/07/logarithmic-depth-buffer-optimizations.html
