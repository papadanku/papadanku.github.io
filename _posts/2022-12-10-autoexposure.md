---
layout: post
title: "Using Hardware Blending to Smooth Auto-Exposure"
---

Some graphics pipelines use 2 textures and 3 passes for auto-exposure. 1 pass to store previous average brightness, 1 pass to generate current average brightness, and 1 pass for temporally smooth average brightnesses and calculate auto-exposure.

We can use the GPU’s blending hardware to generate and temporally smooth the screen’s average brightness in 1 pass. Afterward, we use the second pass to calculate auto-exposure.

```glsl
// Pixel shaders
float4 PS_Blit(VS2PS Input) : COLOR
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
        PixelShader = PS_Blit;
    }

    // Pass1: Get the texture generated from Pass0
    pass ApplyAutoExposure
    {
        // Do autoexposure shading here
    }
}
```