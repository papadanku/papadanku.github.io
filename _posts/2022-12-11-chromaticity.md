---
layout: post
title: "Color Normalization"
---

Images often represent color in 3 channels: `(r,g,b)`. `(r,g,b)` represents the intensities of red, green, and blue. Any number can represent the minimum and maximum intensity of `(r,g,b)`. For this post, **0** is the minimum intensity, while **10** is the maximum intensity.

---

## Scenario

We have **ColorA**, with the color channels of `(0.0, 0.0, 0.1)`. This color is 100% blue, which has an intensity of `0.1`.

### Question

How do we represent the color as 100% “blue”, regardless of its intensity?

### Method

Represent `(r,g,b)` as ratios proportional to the overall color. This is called *normalizing* the color.

### Solution

**Normalization Forumula:** `(r,g,b) / sum(r,g,b)`

Normalizing **ColorA** `(0.0, 0.0, 0.1)`

| Step | Equation |
|------|---------|
| 1 | `(0.0, 0.0, 0.1) / (0.0 + 0.0 + 0.1)` |
| 2 | `(0.0, 0.0, 0.1) / (0.1)` |
| 3 | `(0.0, 0.0, 1.0)` |

**ColorA** is now `(0.0, 0.0, 1.0)`, representing 100% blue.

---

## Source Code

```glsl
float4 NormalizeRGB(sampler SampleColorTex, float2 Tex)
{
    float4 OutputColor = 0.0;
    float4 Color = tex2D(SampleColorTex, Tex);
    float SumRGB = dot(Color.rgb, 1.0);
    float2 Chroma = saturate(Color.xy / SumRGB);
    Chroma = (SumRGB != 0.0) ? Chroma : 1.0 / 3.0;
    return float4(Chroma, 0.0, 1.0);
}
```

---

## Notes on The Source Code

### Dot-Product Optimization

`dot(c.xyz, 1.0)` is an optimization that maps 2 `ADD` instructions to 1 `DP3` instruction

### Chroma Comparison

`(SumRGB != 0.0) ? Chroma : 1.0 / 3.0` is an important line of code.

`(r,g,b)` can sum to 0. Undefined behavior occurs if we divide anything by 0.

We solve this issue by outputting the normalized white point if the sum is 0. We get the normalized white point by normalizing a color with equal **and** non-zero color components. Below is an example on how to compute the normalized white point.

| Step | Equation |
|------|---------|
| 1 | `(1.0, 1.0, 1.0) / (1.0 + 1.0 + 1.0)` |
| 2 | `(1.0, 1.0, 1.0) / (3.0)` |
| 3 | `(1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)` |
