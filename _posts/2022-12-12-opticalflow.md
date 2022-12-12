---
layout: post
title: "Lucas-Kanade Optical Flow in HLSL"
---

Optical flow is the estimation of motion between multiple frames. Optical flow has its application in object detection/recognition, motion estimation, video compression, and video effects.

This post addresses an implementation of Lucas-Kanade optical flow in HLSL.

## Vertex Shader

```c
// Lucas-Kanade optical flow with bilinear fetches

struct APP2VS_LK
{
    float4 Pos : SV_POSITION;
    float4 Tex0 : TEXCOORD0;
};

struct VS2PS_LK
{
    float4 HPos : SV_POSITION;
    float4 Tex0 : TEXCOORD0;
    float4 Tex1 : TEXCOORD1;
    float4 Tex2 : TEXCOORD2;
};

VS2PS_LK GetVertexPyLK(APP2VS Input, float2 PixelSize)
{
    VS2PS_LK Output;
    Output.HPos = Input.Pos;
    Output.Tex0 = Input.Tex0.xyyy + (float4(-1.0, 1.0, 0.0, -1.0) * PixelSize.xyyy);
    Output.Tex1 = Input.Tex0.xyyy + (float4( 0.0, 1.0, 0.0, -1.0) * PixelSize.xyyy);
    Output.Tex2 = Input.Tex0.xyyy + (float4( 1.0, 1.0, 0.0, -1.0) * PixelSize.xyyy);
    return Output;
}
```

## Pixel Shader

### Glossary

| Sampler | Description | Channels |
|---------|-------------|:--------:|
| `SampleV` | Motion vectors from coarser level | `2` |
| `SampleI0` | Image 0 in RG chromaticity | `2` |
| `SampleI1` | Image 1 in RG chromaticity | `2` |
| `SampleG` | Gradients of `SampleI1` | `4` |

```c
/*
    Calculate Lucas-Kanade optical flow by solving (A^-1 * B)
    [A11 A12]^-1 [-B1] -> [ A11 -A12] [-B1]
    [A21 A22]^-1 [-B2] -> [-A21  A22] [-B2]
    A11 = Ix^2
    A12 = IxIy
    A21 = IxIy
    A22 = Iy^2
    B1 = IxIt
    B2 = IyIt
*/

struct Texel
{
    float2 Size;
    float2 LOD;
};

struct UnpackedTex
{
    float4 Tex;
    float4 WarpedTex;
};

void UnpackTex(in Texel Tx, in float4 Tex, in float2 Vectors, out UnpackedTex Output[3])
{
    // Calculate texture attributes of each packed column of tex
    float4 WarpPackedTex = 0.0;
    // Warp horizontal texture coordinates with horizontal motion vector
    WarpPackedTex.x = Tex.x + (Vectors.x * Tx.Size.x);
    // Warp vertical texture coordinates with vertical motion vector
    WarpPackedTex.yzw = Tex.yzw + (Vectors.yyy * Tx.Size.yyy);

    // Unpack and assemble the column's texture coordinates
    // Outputs float4(Tex, 0.0, LOD) in 1 MAD
    const float4 TexMask = float4(1.0, 1.0, 0.0, 0.0);
    Output[0].Tex = (Tex.xyyy * TexMask) + Tx.LOD.xxxy;
    Output[1].Tex = (Tex.xzzz * TexMask) + Tx.LOD.xxxy;
    Output[2].Tex = (Tex.xwww * TexMask) + Tx.LOD.xxxy;

    Output[0].WarpedTex = (WarpPackedTex.xyyy * TexMask) + Tx.LOD.xxxy;
    Output[1].WarpedTex = (WarpPackedTex.xzzz * TexMask) + Tx.LOD.xxxy;
    Output[2].WarpedTex = (WarpPackedTex.xwww * TexMask) + Tx.LOD.xxxy;
}

// [0,1] -> [DestSize.x, DestSize.y]
float2 DecodeVectors(float2 Vectors, float2 ImgSize)
{
    return Vectors * ImgSize;
}

// [DestSize.x, DestSize.y] -> [0,1]
float2 EncodeVectors(float2 Vectors, float2 ImgSize)
{
    return Vectors / ImgSize;
}

float2 GetPixelPyLK
(
    VS2PS_LK Input,
    sampler2D SampleV,
    sampler2D SampleI0,
    sampler2D SampleI1,
    sampler2D SampleG,
    float2 Vectors,
    bool CoarseLevel
)
{
    // Calculate main texel information (TexelSize, TexelLOD)
    Texel Tx;
    float2 MainTex = Input.Tex1.xz;
    float2 Ix = ddx(MainTex);
    float2 Iy = ddy(MainTex);
    float2 DPX = dot(Ix, Ix);
    float2 DPY = dot(Iy, Iy);
    Tx.Size.x = Ix.x;
    Tx.Size.y = Iy.y;
    // log2(x^n) = n*log2(x)
    Tx.LOD = float2(0.0, 0.5) * log2(max(DPX, DPY));
    float2 InvTxSize = 1.0 / Tx.Size;

    // The spatial(S) and temporal(T) derivative neighbors to sample
    const int WindowSize = 9;
    UnpackedTex TexA[3];
    UnpackedTex TexB[3];
    UnpackedTex TexC[3];
    UnpackTex(Tx, Input.Tex0, Vectors, TexA);
    UnpackTex(Tx, Input.Tex1, Vectors, TexB);
    UnpackTex(Tx, Input.Tex2, Vectors, TexC);
    UnpackedTex Pixel[WindowSize] =
    {
        TexA[0], TexA[1], TexA[2],
        TexB[0], TexB[1], TexB[2],
        TexC[0], TexC[1], TexC[2],
    };

    // Windows matrices to sum
    float3 A = 0.0;
    float2 B = 0.0;

    float Determinant = 0.0;
    float2 MotionVectors = 0.0;

    // Decode written vectors from coarser level
    Vectors = tex2Dlod(SampleV, Pixel[5].Tex)
    Vectors = DecodeVectors(Vectors, InvTxSize * 0.5);

    // Calculate residual from previous run
    float2 R = 0.0;
    R += tex2Dlod(SampleI1, Pixel[5].WarpedTex).rg;
    R -= tex2Dlod(SampleI0, Pixel[5].Tex).rg;
    R = pow(abs(R), 2.0);

    bool2 Converged = false;

    if((CoarseLevel == false) && (R.r < 0.5))
    {
        Converged.r = true;
    }

    if((CoarseLevel == false) && (R.g < 0.5))
    {
        Converged.g = true;
    }

    [branch]
    if(Converged.r == false)
    {
        [unroll]
        for(int i = 0; i < WindowSize; i++)
        {
            // B.x = B1; B.y = B2
            float I1 = tex2Dlod(SampleI1, Pixel[i].WarpedTex).r;
            float I0 = tex2Dlod(SampleI0, Pixel[i].Tex).r;
            float IT = I0 - I1;

            // A.x = A11; A.y = A22; A.z = A12/A22
            float2 G = tex2Dlod(SampleG, Pixel[i].Tex).xz;
            A.xyz += (G.xyx * G.xyy);
            B.xy += (G.xy * IT);
        }
    }

    [branch]
    if(Converged.g == false)
    {
        [unroll]
        for(int i = 0; i < WindowSize; i++)
        {
            // B.x = B1; B.y = B2
            float I1 = tex2Dlod(SampleI1, Pixel[i].WarpedTex).g;
            float I0 = tex2Dlod(SampleI0, Pixel[i].Tex).g;
            float IT = I0 - I1;

            // A.x = A11; A.y = A22; A.z = A12/A22
            float2 G = tex2Dlod(SampleG, Pixel[i].Tex).yw;
            A.xyz += (G.xyx * G.xyy);
            B.xy += (G.xy * IT);
        }
    }

    // Create -IxIy (A12) for A^-1 and its determinant
    A.z = -A.z;

    // Make determinant non-zero
    A.xy = A.xy + FP16_SMALLEST_SUBNORMAL;

    // Calculate A^-1 determinant
    Determinant = ((A.x * A.y) - (A.z * A.z));

    // Solve A^-1
    A = A / Determinant;

    // Calculate Lucas-Kanade matrix
    MotionVectors = mul(-B.xy, float2x2(A.yzzx));
    MotionVectors = (Determinant != 0.0) ? MotionVectors : 0.0;

    // Propagate and encode vectors
    MotionVectors = EncodeVectors(Vectors + MotionVectors, InvTxSize);
    return MotionVectors;
}
```
