---
layout: post
title: "Color Normalization"
---

Images often represent color in 3 channels: `(R,G,B)` - red, green, blue. Any number can represent `(R,G,B)`'s minimum and maximum intensity. For this post, **0.0** is the minimum intensity, while **1.0** is the maximum intensity.


## Chromaticity

We have **ColorA**, with an RGB of `(0.0, 0.0, 0.1)`. **ColorA** is 100% blue with an intensity of `0.1`. How do we represent **ColorA** as 100% blue, regardless of its intensity? The answer: we represent `(R,G,B)` as ratios proportional to the overall color. This is called *normalizing* the color, or getting the color's chromaticity.

We get a color's **chromaticity** using `(R,G,B)/(R+G+B)`. Here is a table that highlights the steps to normalize **ColorA** in order to get its chromaticity.

| Step | Equation |
|------|----------|
|   | `(r,g,b) / sum(r,g,b)` |
| 1 | `(0.0, 0.0, 0.1) / (0.0 + 0.0 + 0.1)` |
| 2 | `(0.0, 0.0, 0.1) / (0.1)` |
| 3 | `(0.0, 0.0, 1.0)` |

**ColorA**'s chromaticity  is `(0.0, 0.0, 1.0)`, representing 100% blue.

## Chromaticity Vector Table

Below is a table representing the meaning of multiple chromaticity vector.

| RGB Chromaticity | Meaning |
|------------------|---------|
| `(1.0, 0.0, 0.0)` | 100% red |
| `(0.0, 1.0, 0.0)` | 100% green |
| `(0.0, 0.0, 1.0)` | 100% blue |

RGB chromaticity has a characteristic where all channels must sum to **1.0**. Thus, we can represent RGB chromaticity in 2 channels called **RG Chromaticity**.

| RG Chromaticity | Meaning |
|-----------------|---------|
| `(1.0, 0.0)` | 100% red |
| `(0.0, 1.0)` | 100% green |
| `(0.0, 0.0)` | 100% blue |

## Source Code

```glsl
float3 NormalizeRGB(float3 Color)
{
    float SumRGB = dot(Color, 1.0);
    float3 Chromaticity = saturate(Color / SumRGB);
    Chromaticity = (SumRGB != 0.0) ? Chromaticity : 1.0 / 3.0;
    return Chromaticity;
}
```

## Notes

### Dot-Product Optimization

`dot(c.xyz, 1.0)` is an optimization that maps 2 `ADD` instructions to 1 `DP3` instruction

### Chroma Comparison

`(SumRGB != 0.0) ? Chroma : 1.0 / 3.0` is an important line of code. Undefined behavior occurs if we divide color with a sum of 0. 

We solve this issue by outputting the normalized white point if the sum is 0. We get the normalized white point by normalizing a color with equal **and** non-zero color channels.

## Calculating Normalized White-Point

Here is an example on how to compute the normalized white point.

| Step | Equation |
|------|----------|
|   | `(r,g,b) / sum(r,g,b)` |
| 1 | `(1.0, 1.0, 1.0) / (1.0 + 1.0 + 1.0)` |
| 2 | `(1.0, 1.0, 1.0) / (3.0)` |
| 3 | `(1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)` |
