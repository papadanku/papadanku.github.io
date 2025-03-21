Temporal Auto-Exposure with Hardware Blending
=============================================

Traditional auto-exposure pipelines often involve multiple passes and textures:

Textures
   #. Previous average brightness.
   #. Current average brightness.

Passes
   #. Store the previous average brightness.
   #. Generate the current average brightness.
   #. Smooth the average brightnesses and compute auto-exposure.

This document demonstrates how to optimize this process using hardware blending:

Textures
   #. Combined average brightnesses (previous + current).

Passes
   #. Generate and smooth the average brightnesses.
   #. Compute auto-exposure.

.. code-block:: none
   :caption: Source Code

   /*
      Automatic exposure shader using hardware blending.
   */

   /*
      Vertex shaders.
   */

   struct APP2VS
   {
      float4 HPos : POSITION;
      float2 Tex0 : TEXCOORD0;
   };

   struct VS2PS
   {
      float4 HPos : POSITION;
      float2 Tex0 : TEXCOORD0;
   };

   VS2PS VS_Quad(APP2VS Input)
   {
      VS2PS Output;
      Output.HPos = Input.HPos;
      Output.Tex0 = Input.Tex0;
      return Output;
   }

   /*
      Pixel shaders.

      ---

      AutoExposure(): https://knarkowicz.wordpress.com/2016/01/09/automatic-exposure/
   */

   float3 GetAutoExposure(float3 Color, float2 Tex)
   {
      float LumaAverage = exp(tex2Dlod(SampleLumaTex, float4(Tex, 0.0, 99.0)).r);
      float Ev100 = log2(LumaAverage * 100.0 / 12.5);
      Ev100 -= _ManualBias; // Optional manual bias.
      float Exposure = 1.0 / (1.2 * exp2(Ev100));
      return Color * Exposure;
   }

   float4 PS_GenerateAverageLuma(VS2PS Input) : COLOR0
   {
      float4 Color = tex2D(SampleColorTex, Input.Tex0);
      float3 Luma = max(Color.r, max(Color.g, Color.b));

      // OutputColor0.rgb = Highest brightness from red/green/blue components.
      // OutputColor0.a = Weight for temporal blending.
      float Delay = 1e-3 * _Frametime;
      return float4(log(max(Luma.rgb, 1e-2)), saturate(Delay * _SmoothingSpeed));
   }

   float3 PS_Exposure(VS2PS Input) : COLOR0
   {
      float4 Color = tex2D(SampleColorTex, Input.Tex0);
      return GetAutoExposure(Color.rgb, Input.Tex0);
   }

   technique AutoExposure
   {
      // Pass0: Renders to a self-blending texture.
      // NOTE: Ensure no other shader overwrites this texture.
      pass GenerateAverageLuma
      {
            // Enable hardware blending.
            BlendEnable = TRUE;
            BlendOp = ADD;
            SrcBlend = SRCALPHA;
            DestBlend = INVSRCALPHA;

            VertexShader = VS_Quad;
            PixelShader = PS_GenerateAverageLuma;
      }

      // Pass1: Applies auto-exposure using the texture from Pass0.
      pass ApplyAutoExposure
      {
            VertexShader = VS_Quad;
            PixelShader = PS_Exposure;
      }
   }