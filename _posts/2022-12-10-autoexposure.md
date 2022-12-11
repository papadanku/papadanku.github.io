---
layout: post
title: "Temporal Auto-Exposure with Hardware Blending"
---

Some graphics pipelines have the followng auto-exposure routine
- 2 textures
  1. Previous average brightness
  2. Current average brightness
- 3 passes
  1. Store previously generated average brightness
  2. Generates current average brightness
  3. Smooth average brightnesses and calculate auto-exposure

We can use hardware blending to do the same routine
- 1 texture
  1. Previous + Current average brighness
- 2 Passes
  1. Generate and smooth average brightnesses
  2. Calculate auto-exposure

## Source Code

```c
// Generate average luma that mipmaps to 1x1
float4 PS_GenerateAverageLuma(VS2PS Input) : COLOR
{
    float4 Color = tex2D(SampleColorTex, Input.Tex0);

    // Use alpha to output weight for temporal smoothing
    return float4(max(Color.r, max(Color.g, Color.b)).rrr, _TimeRate);
}

technique AutoExposure
{
    // Pass0: This shader renders to a texture that blends itself
    // NOTE: Do not have another shader overwrite the texture
    pass GenerateAverageLuma
    {
        // Use hardware blending
        BlendEnable = TRUE;
        BlendOp = ADD;
        SrcBlend = INVSRCALPHA;
        DestBlend = SRCALPHA;

        VertexShader = VS_Quad; // Placeholder vertex shader
        PixelShader = PS_GenerateAverageLuma;
    }

    // Pass1: Get the texture generated from Pass0
    pass ApplyAutoExposure
    {
        // Do autoexposure shading here
    }
}
```