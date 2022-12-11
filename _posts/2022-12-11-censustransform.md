---
layout: post
title: "Census Transform in HLSL"
---

A census transform represents the pixel’s relationship with it’s 8-pixel neighborhood in a binary string. The binary string will be 0000000 if the center pixel is lesser than all of its neighbors. The binary string will be 11111111 if the center pixel is greater than or equal to all of its neighbors.

The census transform is invariant to illumination because it does not depend on the image’s actual intensity.

## Source Code

```c
float GetGreyScale(float3 Color)
{
    return max(max(Color.r, Color.g), Color.b);
}

float GetCensusTransform(sampler SampleImage, float2 Tex, float2 PixelSize)
{
    float OutputColor = 0.0;

    const int Neighbors = 8;
    float SampleNeighbor[Neighbors];
    SampleNeighbor[0] = GetGreyScale(tex2D(SampleImage, Tex + (float2(-1.0, +1.0) * PixelSize)).rgb);
    SampleNeighbor[1] = GetGreyScale(tex2D(SampleImage, Tex + (float2( 0.0, +1.0) * PixelSize)).rgb);
    SampleNeighbor[2] = GetGreyScale(tex2D(SampleImage, Tex + (float2(+1.0, +1.0) * PixelSize)).rgb);
    SampleNeighbor[3] = GetGreyScale(tex2D(SampleImage, Tex + (float2(-1.0,  0.0) * PixelSize)).rgb);
    SampleNeighbor[4] = GetGreyScale(tex2D(SampleImage, Tex + (float2(+1.0,  0.0) * PixelSize)).rgb);
    SampleNeighbor[5] = GetGreyScale(tex2D(SampleImage, Tex + (float2(-1.0, -1.0) * PixelSize)).rgb);
    SampleNeighbor[6] = GetGreyScale(tex2D(SampleImage, Tex + (float2( 0.0, -1.0) * PixelSize)).rgb);
    SampleNeighbor[7] = GetGreyScale(tex2D(SampleImage, Tex + (float2(+1.0, -1.0) * PixelSize)).rgb);
    float CenterSample = GetGreyScale(tex2D(SampleImage, Tex).rgb);

    // Generate 8-bit integer from the 8-pixel neighborhood
    for(int i = 0; i < Neighbors; i++)
    {
        float Comparison = step(SampleNeighbor[i], CenterSample);
        OutputColor += ldexp(Comparison, i);
    }

    // Convert the 8-bit integer to float, and average the results from each channel
    return OutputColor * (1.0 / (exp2(8) - 1));
}
```
